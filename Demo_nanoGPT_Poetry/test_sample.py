"""
Sample from a trained model and extract detailed intermediate outputs.
"""
import os
import pickle
from contextlib import nullcontext
import torch
import tiktoken
from model import GPTConfig, GPT
'''
# 加载 state_dict
state_dict = torch.load('yourpath.pt')
print(state_dict.keys())  # 查看保存的参数名称

print(state_dict)
'''
# -----------------------------------------------------------------------------
init_from = 'resume'  # 'resume' or a gpt2 variant (e.g. 'gpt2-xl')
out_dir = 'out'  # ignored if init_from is not 'resume'
start = "\n朝辞白帝" # Start prompt
num_samples = 1  # Number of samples
max_new_tokens = 1  # Only predict the next token
temperature = 0.8  # Sampling temperature
top_k = None  # Top-k sampling
seed = 1337
device = 'cuda'  # Use CUDA if available
dtype = 'float32'  # 'float32', 'float16', or 'bfloat16'
compile = False  # Compile the model for faster inference (requires PyTorch 2.0)
exec(open('configurator.py').read())  # Overrides from command line or config file
# -----------------------------------------------------------------------------

torch.manual_seed(seed)
torch.cuda.manual_seed(seed)
torch.backends.cuda.matmul.allow_tf32 = True
torch.backends.cudnn.allow_tf32 = True
device_type = 'cuda' if 'cuda' in device else 'cpu'
ptdtype = {'float32': torch.float32, 'float16': torch.float16, 'bfloat16': torch.bfloat16}[dtype]
ctx = nullcontext() if device_type == 'cpu' else torch.amp.autocast(device_type=device_type, dtype=ptdtype)

# Load the model
if init_from == 'resume':
    ckpt_path = os.path.join(out_dir, 'ckpt.pt')
    checkpoint = torch.load(ckpt_path, map_location=device)
    gptconf = GPTConfig(**checkpoint['model_args'])
    model = GPT(gptconf)
    state_dict = checkpoint['model']
    unwanted_prefix = '_orig_mod.'
    for k, v in list(state_dict.items()):
        if k.startswith(unwanted_prefix):
            state_dict[k[len(unwanted_prefix):]] = state_dict.pop(k)
    model.load_state_dict(state_dict)
elif init_from.startswith('gpt2'):
    model = GPT.from_pretrained(init_from, dict(dropout=0.0))

model.eval()
model.to(device)
if compile:
    model = torch.compile(model)

# Load tokenizer metadata
load_meta = False
if init_from == 'resume' and 'config' in checkpoint and 'dataset' in checkpoint['config']:
    meta_path = os.path.join('data', checkpoint['config']['dataset'], 'meta.pkl')
    load_meta = os.path.exists(meta_path)

if load_meta:
    print(f"Loading meta from {meta_path}...")
    with open(meta_path, 'rb') as f:
        meta = pickle.load(f)
    stoi, itos = meta['stoi'], meta['itos']
    encode = lambda s: [stoi[c] for c in s]
    decode = lambda l: ''.join([itos[i] for i in l])
else:
    print("No meta.pkl found, assuming GPT-2 encodings...")
    enc = tiktoken.get_encoding("gpt2")
    encode = lambda s: enc.encode(s, allowed_special={"<|endoftext|>"})
    decode = lambda l: enc.decode(l)

# Encode the input prompt
if start.startswith('FILE:'):
    with open(start[5:], 'r', encoding='utf-8') as f:
        start = f.read()
start_ids = encode(start)
x = torch.tensor(start_ids, dtype=torch.long, device=device)[None, ...]

# Generate output and extract details with custom top_k and rounds
def generate_with_details(model, x, decode, num_rounds=5, top_k=5, temperature=1.0):
    """
    Generate tokens step by step, printing detailed outputs like QKV and attention matrices.
    Args:
        model: The trained model.
        x: The input prompt encoded as tensor.
        decode: A function to decode tokens to text.
        num_rounds: Number of tokens to generate.
        top_k: Number of top tokens to consider for probabilities.
        temperature: Temperature for softmax scaling.
    """
    for round_idx in range(num_rounds):
        with torch.no_grad():
            # Forward pass with detailed outputs
            logits, _, details = model(x, return_details=True)

            # Decode the input prompt
            input_prompt = decode(x[0].tolist())
            print(f"Round {round_idx + 1} | Input Prompt: {input_prompt}")
            print("---------------")
            print("Detailed Outputs:")

            # Print detailed information per layer
            for i, layer_details in enumerate(details["layer_details"]):
                print(f"Layer {i + 1}:")
                print(f"  Q: {layer_details['attn_details']['q'].shape}")
                print(f"  K: {layer_details['attn_details']['k'].shape}")
                print(f"  V: {layer_details['attn_details']['v'].shape}")
                print(f"  Attention Weights: {layer_details['attn_details']['attention_weights'].shape}")
                print(f"  Attention Output: {layer_details['attn_details']['attention_output'].shape}")
                print(f"  MLP Input: {layer_details['mlp_input'].shape}")
                print(f"  MLP Output: {layer_details['mlp_output'].shape}")
                print(f"  Residual Output: {layer_details['residual_output'].shape}")
                print("---------------")

            # Extract final logits and probabilities
            final_logits = details["final_logits"][:, -1, :]  # Only consider the last token
            final_logits = final_logits / temperature  # Apply temperature scaling

            # Compute probabilities
            probs = torch.softmax(final_logits, dim=-1)

            # Get top_k tokens and their probabilities
            top_k_probs, top_k_indices = torch.topk(probs, top_k, dim=-1)
            top_k_tokens = [decode([idx.item()]) for idx in top_k_indices[0]]
            print("Top K Tokens and Probabilities:")
            for token, prob in zip(top_k_tokens, top_k_probs[0]):
                print(f"  Token: {token}, Probability: {prob.item():.4f}")

            # Select the most probable token (argmax strategy)
            next_token = top_k_indices[0, 0].item()
            predicted_token = decode([next_token])
            print(f"Predicted Next Token: {predicted_token}")
            print("---------------")

            # Append the next token to the input sequence
            next_token_tensor = torch.tensor([[next_token]], device=x.device, dtype=torch.long)
            x = torch.cat((x, next_token_tensor), dim=1)

    print(f"Final Generated Sequence: {decode(x[0].tolist())}")


# Example usage
with torch.no_grad():
    with ctx:
        generate_with_details(
            model=model,
            x=x,
            decode=decode,
            num_rounds=5,  # Set number of tokens to generate
            top_k=5,       # Set top_k for probabilities
            temperature=1.0  # Temperature for softmax
        )


#python test_sample.py --out_dir=out-shakespeare-char