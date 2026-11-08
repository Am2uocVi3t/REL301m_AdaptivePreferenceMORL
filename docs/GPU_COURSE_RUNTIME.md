# D-drive CUDA runtime (course completion v2)

The CPU demo environment `.venv` remains separate. This optional training
environment is `artifacts/gpu-runtime`, Python 3.11.18, Torch 2.14.1+cu130 and
Torchvision 0.29.1+cu130 from the official PyTorch wheel index. All other installed
packages follow `artifacts/runtime/windows-core-requirements.txt`; exact Box2D
2.3.8 comes from the verified local native wheel. `pycddlib==2.1.6` remains
unavailable, so GPI-LS is not qualified. An import alone is not a CUDA witness.

From the repository root in PowerShell, execute verbatim:

```powershell
. scripts/use_d_runtime.ps1
artifacts/gpu-runtime/Scripts/python.exe -c "import torch; torch.manual_seed(31); x=torch.randn(64,256,device='cuda',requires_grad=True); y=(x@x.T).square().mean(); y.backward(); assert torch.isfinite(x.grad).all(); print('CUDA_WITNESS',torch.__version__,torch.cuda.get_device_name(),float(y.detach()),float(x.grad.norm()))"
```

Expected: `CUDA_WITNESS 2.14.1+cu130 NVIDIA GeForce RTX 3050 Laptop GPU`,
finite loss near 1277.6865 and finite gradient norm near 43.0354. This proves a
real seeded forward/backward on the device, not convergence or cross-device
bitwise reproducibility. Run the bounded Envelope smoke on both CPU and CUDA
before choosing a device for this small-network workload. Do not assume GPU
is faster. No scientific split, reward scale, reference point or budget changes
when switching devices.

The portable LaTeX compiler is `artifacts/latex-runtime/tectonic.exe` (0.17.0,
GitHub release digest verified). Set `TECTONIC_CACHE_DIR` to
`artifacts/runtime/tectonic` as an absolute D-drive path. Use the HTTPS bundle
`https://data1b.fullyjustified.net/tlextras-2022.0r0.tar`; the default relay
can redirect its client to a blocked HTTP endpoint. This is a transport fix,
not a workaround for access controls. The initial unchanged group template
compiled successfully to `artifacts/latex-initial-check/main.pdf`.
