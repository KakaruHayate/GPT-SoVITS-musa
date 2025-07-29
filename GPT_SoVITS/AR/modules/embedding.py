# modified from https://github.com/lifeiteng/vall-e/blob/main/valle/modules/embedding.py
import math

import torch
from torch import nn


class TokenEmbedding(nn.Module):
    def __init__(
        self,
        embedding_dim: int,
        vocab_size: int,
        dropout: float = 0.0,
    ):
        super().__init__()

        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim

        self.dropout = torch.nn.Dropout(p=dropout)
        self.word_embeddings = nn.Embedding(self.vocab_size, self.embedding_dim)

    @property
    def weight(self) -> torch.Tensor:
        return self.word_embeddings.weight

    def embedding(self, index: int) -> torch.Tensor:
        return self.word_embeddings.weight[index : index + 1]

    def forward(self, x: torch.Tensor):
        x = self.word_embeddings(x)
        x = self.dropout(x)
        return x


class SinePositionalEmbeddingOLD(nn.Module):
    def __init__(
        self,
        embedding_dim: int,
        dropout: float = 0.0,
        scale: bool = False,
        alpha: bool = False,
    ):
        super().__init__()
        self.embedding_dim = embedding_dim
        self.x_scale = math.sqrt(embedding_dim) if scale else 1.0
        self.alpha = nn.Parameter(torch.ones(1), requires_grad=alpha)
        self.dropout = torch.nn.Dropout(p=dropout)

        self.reverse = False
        self.pe = None
        self.extend_pe(torch.tensor(0.0).expand(1, 4000))

    def extend_pe(self, x):
        """Reset the positional encodings."""
        if self.pe is not None:
            if self.pe.size(1) >= x.size(1):
                if self.pe.dtype != x.dtype or self.pe.device != x.device:
                    self.pe = self.pe.to(dtype=x.dtype, device=x.device)
                return
        pe = torch.zeros(x.size(1), self.embedding_dim)
        if self.reverse:
            position = torch.arange(x.size(1) - 1, -1, -1.0, dtype=torch.float32).unsqueeze(1)
        else:
            position = torch.arange(0, x.size(1), dtype=torch.float32).unsqueeze(1)
        div_term = torch.exp(
            torch.arange(0, self.embedding_dim, 2, dtype=torch.float32) * -(math.log(10000.0) / self.embedding_dim)
        )
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)
        self.pe = pe.to(device=x.device, dtype=x.dtype).detach()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        self.extend_pe(x)
        output = x.unsqueeze(-1) if x.ndim == 2 else x
        output = output * self.x_scale + self.alpha * self.pe[:, : x.size(1)]
        return self.dropout(output)


class SinePositionalEmbedding(nn.Module):
    def __init__(
        self,
        embedding_dim: int,
        dropout: float = 0.0,
        scale: bool = False,
        alpha: bool = False,
    ):
        super().__init__()
        self.embedding_dim = embedding_dim
        self.x_scale = math.sqrt(embedding_dim) if scale else 1.0
        self.alpha = nn.Parameter(torch.ones(1), requires_grad=alpha)
        self.dropout = torch.nn.Dropout(p=dropout)

        self.reverse = False
        self.pe = None
        # 预先分配一个较大的缓冲区，避免频繁重新计算
        # 初始大小可以根据你的最大序列长度来定
        self.extend_pe(torch.tensor(0.0).expand(1, 4000)) 

    def extend_pe(self, x, past_kv_len=0): # <<<--- [修改1] 增加 past_kv_len 参数
        """Reset the positional encodings."""
        # 计算需要的总长度
        needed_len = x.size(1) + past_kv_len # <<<--- [修改2] 计算总长度
        
        if self.pe is not None and self.pe.size(1) >= needed_len:
            if self.pe.dtype != x.dtype or self.pe.device != x.device:
                self.pe = self.pe.to(dtype=x.dtype, device=x.device)
            return
            
        # 如果需要，重新计算pe矩阵以覆盖所需长度
        # position现在代表绝对位置
        pe = torch.zeros(needed_len, self.embedding_dim)
        if self.reverse:
            # reverse 逻辑可能需要根据具体需求调整，但对于TTS通常为False
            position = torch.arange(needed_len - 1, -1, -1.0, dtype=torch.float32).unsqueeze(1)
        else:
            position = torch.arange(0, needed_len, dtype=torch.float32).unsqueeze(1) # <<<--- [修改3] 使用 needed_len
            
        div_term = torch.exp(
            torch.arange(0, self.embedding_dim, 2, dtype=torch.float32) * -(math.log(10000.0) / self.embedding_dim)
        )
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)
        self.pe = pe.to(device=x.device, dtype=x.dtype).detach()

    # <<<--- [修改4] 在 forward 的签名中加入 past_kv_len
    def forward(self, x: torch.Tensor, past_kv_len: int = 0) -> torch.Tensor:
        """
        x: The input tensor.
        past_kv_len: The length of the past key-value cache, used as an offset for positions.
        """
        # <<<--- [修改5] 将 past_kv_len 传递给 extend_pe
        self.extend_pe(x, past_kv_len=past_kv_len)
        
        output = x.unsqueeze(-1) if x.ndim == 2 else x
        
        # <<<--- [修改6] 使用切片来获取正确的位置编码段
        start_pos = past_kv_len
        end_pos = past_kv_len + x.size(1)
        output = output * self.x_scale + self.alpha * self.pe[:, start_pos:end_pos]
        
        return self.dropout(output)