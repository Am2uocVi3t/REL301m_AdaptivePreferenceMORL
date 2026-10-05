import torch
import numpy as np
from src.models.q_network import VectorQNetwork

def compute_bootstrap_uncertainty(
    q_network: VectorQNetwork,
    states_batch: torch.Tensor,
    preference: np.ndarray,
    device: str = "cpu"
) -> float:
    """
    Computes Bootstrap Ensemble Uncertainty u(w) as defined in Eq. (12):
    u(w) = E_{s ~ B} [ Var_{k=1}^K ( w^T Q_{theta_k}(s, a_k^*, w) ) ]
    
    Args:
        q_network: VectorQNetwork with K bootstrap heads
        states_batch: Tensor of sampled states [B, state_dim]
        preference: 1D array of shape [reward_dim]
        device: PyTorch device
    Returns:
        uncertainty: Scalar float indicating epistemic variance across heads
    """
    q_network.eval()
    with torch.no_grad():
        B = states_batch.size(0)
        w_tensor = torch.as_tensor(preference, dtype=torch.float32, device=device).unsqueeze(0).repeat(B, 1)
        
        # Forward pass: shape [K, B, action_dim, reward_dim]
        all_q = q_network(states_batch.to(device), w_tensor)
        K, _, action_dim, reward_dim = all_q.shape

        # For each head k, compute scalarized values: w^T Q_k(s, a, w) -> [K, B, action_dim]
        # all_q: [K, B, action_dim, reward_dim], w_tensor: [B, reward_dim]
        scalarized = torch.einsum("kbad,bd->kba", all_q, w_tensor)

        # Max over actions for each head: a_k^* = argmax_a w^T Q_k(s, a, w) -> [K, B]
        max_q_per_head, _ = torch.max(scalarized, dim=-1)

        # Variance across K heads: [B]
        variance_per_state = torch.var(max_q_per_head, dim=0, unbiased=True)

        # Expectation over sampled batch of states
        uncertainty = torch.mean(variance_per_state).item()

    return float(uncertainty)
