import torch

from fglc.models import BeliefMemory, Encoder, GroupedDynamics, RewardHead, ValueHead


B = 4
T = 8
D_X = 10
D_A = 4
K = 6
D = 32
H_DIM = 128


def _inputs() -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    state = torch.randn(B, T, D_X)
    action = torch.randn(B, T, D_A)
    reward = torch.randn(B, T)
    return state, action, reward


def _modules() -> tuple[Encoder, BeliefMemory, GroupedDynamics, RewardHead, ValueHead]:
    return (
        Encoder(D_x=D_X, K=K, d=D),
        BeliefMemory(K=K, d=D, D_a=D_A, h_dim=H_DIM),
        GroupedDynamics(K=K, d=D, D_a=D_A, h_dim=H_DIM),
        RewardHead(K=K, d=D, D_a=D_A, h_dim=H_DIM),
        ValueHead(K=K, d=D, h_dim=H_DIM),
    )


def test_encoder_shape():
    state, _, _ = _inputs()
    encoder = Encoder(D_x=D_X, K=K, d=D)

    assert encoder(state).shape == (B, T, K, D)


def test_belief_shape():
    state, action, reward = _inputs()
    encoder = Encoder(D_x=D_X, K=K, d=D)
    belief = BeliefMemory(K=K, d=D, D_a=D_A, h_dim=H_DIM)

    h = belief(encoder(state), action, reward)

    assert h.shape == (B, T, H_DIM)


def test_dynamics_shape():
    state, action, reward = _inputs()
    encoder = Encoder(D_x=D_X, K=K, d=D)
    belief = BeliefMemory(K=K, d=D, D_a=D_A, h_dim=H_DIM)
    dynamics = GroupedDynamics(K=K, d=D, D_a=D_A, h_dim=H_DIM)
    z = encoder(state)
    h = belief(z, action, reward)

    mu, log_sigma = dynamics(z, action, h)

    assert mu.shape == (B, T, K, D)
    assert log_sigma.shape == (B, T, K, D)


def test_reward_head_shape():
    z_flat = torch.randn(B, T, K * D)
    action = torch.randn(B, T, D_A)
    h = torch.randn(B, T, H_DIM)
    reward_head = RewardHead(K=K, d=D, D_a=D_A, h_dim=H_DIM)

    assert reward_head(z_flat, action, h).shape == (B, T)


def test_value_head_shape():
    z_flat = torch.randn(B, T, K * D)
    h = torch.randn(B, T, H_DIM)
    value_head = ValueHead(K=K, d=D, h_dim=H_DIM)

    assert value_head(z_flat, h).shape == (B, T)


def test_no_nan_forward():
    state, action, reward = _inputs()
    encoder, belief, dynamics, reward_head, value_head = _modules()

    z = encoder(state)
    h = belief(z, action, reward)
    mu, log_sigma = dynamics(z, action, h)
    z_flat = torch.reshape(z, (B, T, K * D))
    reward_pred = reward_head(z_flat, action, h)
    value_pred = value_head(z_flat, h)

    for output in (z, h, mu, log_sigma, reward_pred, value_pred):
        assert torch.isfinite(output).all()


def test_parameter_count():
    modules = _modules()
    total_params = sum(p.numel() for module in modules for p in module.parameters())

    assert total_params < 2_000_000


def test_docstring_source_present():
    import fglc.models.belief as belief
    import fglc.models.dynamics as dynamics
    import fglc.models.encoder as encoder
    import fglc.models.heads as heads

    for module in (encoder, belief, dynamics, heads):
        assert "docs/idea/04_BASE_WORLD_MODEL" in (module.__doc__ or "")
