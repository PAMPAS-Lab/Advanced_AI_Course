import streamlit as st
import torch
import torch.nn.functional as F
import pickle
import plotly.graph_objects as go
import streamlit.components.v1 as components


# 加载模型
@st.cache_resource
def load_model():
    from model import GPTConfig, GPT
    ckpt_path = "out-shakespeare-char/poetry_ckpt.pt"
    checkpoint = torch.load(ckpt_path, map_location="cpu")
    gptconf = GPTConfig(**checkpoint["model_args"])
    model = GPT(gptconf)
    state_dict = checkpoint['model']
    unwanted_prefix = '_orig_mod.'
    for k, v in list(state_dict.items()):
        if k.startswith(unwanted_prefix):
            state_dict[k[len(unwanted_prefix):]] = state_dict.pop(k)
    model.load_state_dict(state_dict)
    return model

# 定义tokenizer和解码器
@st.cache_resource
def load_tokenizer():
    meta_path = "data/shakespeare_char/poetry_meta.pkl"
    with open(meta_path, 'rb') as f:
        meta = pickle.load(f)
        stoi, itos = meta['stoi'], meta['itos']
        encode = lambda s: [stoi[c] for c in s]
        decode = lambda l: ''.join([itos[i] for i in l])
    return encode, decode

# 绘制矩阵作为交互式Heatmap（倒转行坐标）
def plot_matrix(matrix, title, key):
    fig = go.Figure(
        data=go.Heatmap(
            z=matrix,
            colorscale='Viridis',
            colorbar=dict(title="值")
        )
    )
    fig.update_layout(
        title=title,
        xaxis_title="列",
        yaxis_title="行",
        yaxis=dict(autorange="reversed"),  # 倒转行坐标
        xaxis_showgrid=False,
        yaxis_showgrid=False,
    )
    st.plotly_chart(fig, use_container_width=True, key=key)

# 展示注意力矩阵信息（Q, K, V, 注意力权重）
def display_attention_details(model, x, decode,top_k,temperature, selected_layer, selected_head):
    with torch.no_grad():
        logits, _, details = model(x, return_details=True)

        # Decode当前输入
        input_prompt = decode(x[0].tolist())
        st.markdown(
            f"""
            <div style="font-size: 24px; font-weight: bold;">
                当前输入: {input_prompt}
            </div>
            """, unsafe_allow_html=True)
        st.write("---------------")
        
        # 用户选择的层索引，默认显示最后一层
        layer_index = selected_layer if selected_layer != -1 else len(details["layer_details"]) - 1
        layer_details = details["layer_details"][layer_index]

        # 选择头索���，默认选择第一个头
        head_index = selected_head

        # 横向展示 Q, K, V
        st.markdown(f"## **多头注意力 - 层 {layer_index + 1}, 头 {head_index + 1}**")
        cols = st.columns(3)  # 修改为3列布局
        with cols[0]:
            st.markdown("#### Query (Q):")
            plot_matrix(layer_details["attn_details"]["q"][:, head_index, :, :].squeeze().cpu().numpy(), "Query (Q)", key=f"dis_q_layer_{layer_index}_head_{head_index}")
        with cols[1]:
            st.markdown("#### Key (K):")
            plot_matrix(layer_details["attn_details"]["k"][:, head_index, :, :].squeeze().cpu().numpy(), "Key (K)", key=f"dis_k_layer_{layer_index}_head_{head_index}")
        with cols[2]:
            st.markdown("#### Value (V):")
            plot_matrix(layer_details["attn_details"]["v"][:, head_index, :, :].squeeze().cpu().numpy(), "Value (V)", key=f"dis_v_layer_{layer_index}_head_{head_index}")

        # 单独一行展示注意力权重
        st.markdown("#### 注意力权重 (Attention Weights):")
        plot_matrix(
            layer_details["attn_details"]["attention_weights"][:, head_index, :, :].squeeze().cpu().numpy(),
            "Attention Weights",
            key=f"dis_attention_weights_layer_{layer_index}_head_{head_index}"
        )
        # 展示预测的下一个Token概率
        st.markdown("## **预测的下一个单词概率**")
        final_logits = details["final_logits"][:, -1, :]  # 只关注最后一个Token
        final_logits = final_logits / temperature  # 温度调整
        probs = F.softmax(final_logits, dim=-1)

        # 选取概率最高的单词
        #next_token = top_k_indices[0, 0].item()
        #predicted_token = decode([next_token])

        # 获取Top K单词和概率
        top_k_probs, top_k_indices = torch.topk(probs, top_k, dim=-1)
        top_k_tokens = [decode([idx.item()]) for idx in top_k_indices[0]]

        # 如果在session_state中已经存储了上一次的采样结果，使用该结果
        if hasattr(st.session_state, 'current_next_token'):
            next_token = st.session_state.current_next_token
        else:
            # 如果没有，使用概率采样
            sampled_index_within_top_k = torch.multinomial(top_k_probs[0], num_samples=1).item()
            next_token = top_k_indices[0, sampled_index_within_top_k].item()
        
        # 将本次生成的token存储下来
        st.session_state.current_next_token = next_token
        predicted_token = decode([next_token])

        st.markdown("### **Top K 单词及概率:**")
        for token, prob in zip(top_k_tokens, top_k_probs[0]):
            if token == "\n":
                token_show = r"\n(换行)"
            else:
                token_show = token
            
            # 判断是否为预测的下一个token
            if token == predicted_token:
                # 如果是预测的下一个token，整行标蓝显示
                st.markdown(f"#### <span style='color:blue'>单词: {token_show}  , 概率: {prob.item():.4f}</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"#### 单词: {token_show}  , 概率: {prob.item():.4f}")

        st.markdown(f"### **预测下一个单词:** <span style='color:blue'>{predicted_token}</span>", unsafe_allow_html=True)
    
        # 返回更新后的输入序列
        next_token_tensor = torch.tensor([[next_token]], device=x.device, dtype=torch.long)
        return torch.cat((x, next_token_tensor), dim=1)

def main():
    # 主程序布局
    st.set_page_config(layout="wide")  # 设置为宽屏模式

    # 左侧导航栏
    st.sidebar.markdown("# 页面选择")
    page = st.sidebar.radio("", ["参数设置", "nanoGPT可视化展示", "Transformer可视化教程"])

    if page == "参数设置":
        # 左侧参数设置
        st.sidebar.title("参数设置")  # 左侧固定的目录栏
        st.sidebar.markdown("### 输入提示语 (Prompt)")
        prompt = st.sidebar.text_input("请输入您的提示语 (中文):", "白玉为堂金做马",key="prompt_input")

        st.sidebar.markdown("### 模型参数")
        top_k = st.sidebar.slider("选择Top K值:", min_value=1, max_value=10, value=5)
        temperature = st.sidebar.slider("选择Temperature值:", min_value=0.1, max_value=2.0, value=1.0)
        selected_layer = st.sidebar.slider("选择层查看:", min_value=1, max_value=6, value=6)
        selected_head = st.sidebar.slider("选择头查看:", min_value=1, max_value=6, value=1)

        # 初始化输入序列
        encode, decode = load_tokenizer()
        start_ids = encode(prompt)

        # 判断是否需要重新生成token
        if "x" not in st.session_state:
            st.session_state.x = torch.tensor([start_ids], dtype=torch.long)
            st.session_state.previous_prompt = prompt  # 记录当前prompt作为上一个输入
        else:
            # 如果prompt有变化，重新生成token，否则继续生成
            if prompt != st.session_state.previous_prompt:
                st.session_state.x = torch.tensor([start_ids], dtype=torch.long)  # 重置输入
                st.session_state.previous_prompt = prompt  # 更新上一次的prompt



        # 加载模型
        model = load_model()
        model.eval()

        # 右侧内容显示
        st.title("Transformer 可视化解释器")
        st.markdown("### 可视化结果")

        # 在参数设置页面添加session_state管理
        if "previous_next_token" not in st.session_state:
            st.session_state.previous_next_token = None

        # 自动更新视图
        temp = display_attention_details(
            model,
            st.session_state.x,
            decode,
            top_k,
            temperature,
            selected_layer,
            selected_head,
        )

        # 当点击按钮时，清空旧的展示并重新生成视图
        if st.sidebar.button("生成下一个Token"):
            # 删除上一次存储的token，确保下次重新采样
            if hasattr(st.session_state, 'current_next_token'):
                del st.session_state.current_next_token
            
            # 生成新的 token
            st.session_state.x = temp
            st.rerun()  # 强制重新加载页面，清除旧数据
    elif page == "nanoGPT可视化展示":
        # 嵌入网页
        st.sidebar.title("nanoGPT可视化")  # 左侧固定的目录栏
        iframe_url = "https://bbycroft.net/llm"  # 这里替换为你想要嵌入的网页URL
        st.title("nanoGPT可视化展示")
        st.markdown(f"访问网站: [{iframe_url}]({iframe_url})")
        components.iframe(iframe_url, height=1000)
    elif page == "Transformer可视化教程":
        # 设置侧边栏标题
        st.sidebar.title("Transformer可视化教程")
        
        # 定义 iframe 的 URL
        iframe_url = "https://jalammar.github.io/illustrated-transformer/"
        
        # 设置页面标题和链接
        st.title("The Illustrated Transformer")
        st.markdown(f"访问原文: [{iframe_url}]({iframe_url})", unsafe_allow_html=True)
        
        # 定义 iframe 的 HTML 代码，设置高度和样式
        iframe_code = f"""
        <iframe src="{iframe_url}" width="100%" height="800px" style="border:none; overflow:auto;"></iframe>
        """
        
        # 使用 st.markdown 渲染 iframe
        st.markdown(iframe_code, unsafe_allow_html=True)

if __name__ == "__main__":
    main()

    #streamlit run GPT_show.py
    
