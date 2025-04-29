import numpy as np
import torch
import torch.nn.functional as F
import streamlit as st
import matplotlib.pyplot as plt

# 设置matplotlib以支持中文
plt.rcParams['font.family'] = 'SimHei'
plt.rcParams['axes.unicode_minus'] = False

# 定义矩阵可视化函数
def plot_matrix(matrix, title, xticks, yticks, xlabel="维度", ylabel="Token"):
    fig, ax = plt.subplots(figsize=(5, 4))
    cax = ax.matshow(matrix, cmap="viridis")
    fig.colorbar(cax)
    for (i, j), val in np.ndenumerate(matrix):
        ax.text(j, i, f"{val:.2f}", ha="center", va="center", color="white" if val < 0.5 else "black")
    ax.set_xticks(np.arange(len(xticks)))
    ax.set_yticks(np.arange(len(yticks)))
    ax.set_xticklabels(xticks)
    ax.set_yticklabels(yticks)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    st.pyplot(fig)

# Self-Attention计算函数
def self_attention(Q, K, V, scale=True):
    attn_scores = torch.matmul(Q, K.T)  # [seq_len, seq_len]
    if scale:
        dk = K.size(-1)
        st.write(f"注意力分数缩放，缩放因子为: 1/√{dk}")
        attn_scores = attn_scores / torch.sqrt(torch.tensor(dk, dtype=torch.float32))
    attn_weights = F.softmax(attn_scores, dim=-1)
    output = torch.matmul(attn_weights, V)
    return attn_scores, attn_weights, output

# 多头注意力计算函数
def multi_head_attention(X, num_heads, W_q_list, W_k_list, W_v_list, W_o):
    head_outputs = []
    st.subheader("每个头的 Q, K, V 矩阵和输出")
    for i in range(num_heads):
        st.write(f"### 头 {i+1}: 计算 Q, K, V 并进行注意力计算")
        
        # 计算每个头的 Q, K, V 矩阵
        Q = torch.matmul(X, W_q_list[i])
        K = torch.matmul(X, W_k_list[i])
        V = torch.matmul(X, W_v_list[i])
        
        # 展示每个头的 W^Q, W^K, W^V 矩阵在一行
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write(f"W_q - 头 {i+1}")
            plot_matrix(W_q_list[i].detach().numpy(), f"W_q - 头 {i+1}", [f"维度 {j+1}" for j in range(head_dim)], [f"维度 {j+1}" for j in range(dim)], xlabel="维度", ylabel="维度")
        with col2:
            st.write(f"W_k - 头 {i+1}")
            plot_matrix(W_k_list[i].detach().numpy(), f"W_k - 头 {i+1}", [f"维度 {j+1}" for j in range(head_dim)], [f"维度 {j+1}" for j in range(dim)], xlabel="维度", ylabel="维度")
        with col3:
            st.write(f"W_v - 头 {i+1}")
            plot_matrix(W_v_list[i].detach().numpy(), f"W_v - 头 {i+1}", [f"维度 {j+1}" for j in range(head_dim)], [f"维度 {j+1}" for j in range(dim)], xlabel="维度", ylabel="维度")

        # 展示每个头的 Q, K, V 矩阵在一行
        col4, col5, col6 = st.columns(3)
        with col4:
            st.write(f"Q 矩阵 - 头 {i+1}")
            plot_matrix(Q.detach().numpy(), f"Q - 头 {i+1}", [f"维度 {j+1}" for j in range(head_dim)], [f"Token {j+1}" for j in range(seq_len)])
        with col5:
            st.write(f"K 矩阵 - 头 {i+1}")
            plot_matrix(K.detach().numpy(), f"K - 头 {i+1}", [f"维度 {j+1}" for j in range(head_dim)], [f"Token {j+1}" for j in range(seq_len)])
        with col6:
            st.write(f"V 矩阵 - 头 {i+1}")
            plot_matrix(V.detach().numpy(), f"V - 头 {i+1}", [f"维度 {j+1}" for j in range(head_dim)], [f"Token {j+1}" for j in range(seq_len)])


        # 计算注意力
        st.write(f"头 {i+1}: 计算 Q, K, V 并生成注意力权重和输出")
        scores, attn_weights, output = self_attention(Q, K, V, scale=True)
        
        # 展示每个头的输出
        st.write(f"头 {i+1} 的输出")
        plot_matrix(output.detach().numpy(), f"头 {i+1} 的输出", [f"维度 {j+1}" for j in range(head_dim)], [f"Token {j+1}" for j in range(seq_len)])
        head_outputs.append(output)
    
    # 拼接所有头的输出
    concatenated_output = torch.cat(head_outputs, dim=-1)
    st.write("拼接后的输出 (将所有头的输出按列拼接)")
    plot_matrix(concatenated_output.detach().numpy(), "拼接后的输出", [f"维度 {j+1}" for j in range(num_heads * head_dim)], [f"Token {j+1}" for j in range(seq_len)])
    
    # 展示 Wo 矩阵
    st.subheader("线性变换矩阵 W_o")
    plot_matrix(W_o.detach().numpy(), "W_o 矩阵", [f"维度 {j+1}" for j in range(num_heads * head_dim)], [f"维度 {j+1}" for j in range(dim)])
    st.write("将拼接后的结果通过 W_o 线性变换得到最终输出。")
    
    # 线性变换得到最终输出
    final_output = torch.matmul(concatenated_output, W_o)
    st.write("最终输出")
    plot_matrix(final_output.detach().numpy(), "最终输出", [f"维度 {j+1}" for j in range(dim)], [f"Token {j+1}" for j in range(seq_len)])
    
    return final_output, attn_weights

# Streamlit UI
st.title("多头注意力机制逐步可视化")

# 输入序列长度和特征维度
seq_len = st.slider("序列长度", 2, 10, 3)
dim = st.slider("嵌入维度", 2, 10, 4)
num_heads = st.slider("注意力头数量", 1, 4, 2)

# 确保每个头的维度相等
assert dim % num_heads == 0, "嵌入维度必须是注意力头数量的整数倍。"

# 显示输入嵌入矩阵
embedding = torch.randint(0, 2, (seq_len, dim), dtype=torch.float)
st.subheader("输入嵌入矩阵")
plot_matrix(embedding.detach().numpy(), "Embedding Matrix", [f"维度 {i+1}" for i in range(dim)], [f"Token {i+1}" for i in range(seq_len)])

# 生成输入嵌入矩阵和权重矩阵
head_dim = dim // num_heads
W_q_list = [torch.randint(0, 2, (dim, head_dim), dtype=torch.float) for _ in range(num_heads)]
W_k_list = [torch.randint(0, 2, (dim, head_dim), dtype=torch.float) for _ in range(num_heads)]
W_v_list = [torch.randint(0, 3, (dim, head_dim), dtype=torch.float) for _ in range(num_heads)]
W_o = torch.randint(0, 2, (num_heads * head_dim, dim), dtype=torch.float)

# 计算多头注意力输出
multi_head_output, attn_weights = multi_head_attention(embedding, num_heads, W_q_list, W_k_list, W_v_list, W_o)

# 使用命令运行：streamlit run multihead_self_attention_demo.py
