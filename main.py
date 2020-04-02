import torch
import torch.nn as nn
import torch.nn.functional as F
from FunctionsNd import ConvNd
from FunctionsNd import ConvTransposeNd
import time
import matplotlib.pyplot as plt
torch.backends.cudnn.deterministic = True

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Define 3D tensor to test on
inChans = 1
outChans = 1
x = torch.rand(1, inChans, 51, 51, 51).to(device)
ks = 3
padding = 3
# Only zeros allowed by pytorch
padding_mode = 'zeros'
stride = 1
weight = 2
bias = 2

# ConvNd where d = 3
conv = ConvNd(inChans, outChans, 3, ks, stride, padding, use_bias=True, padding_mode=padding_mode, 
kernel_initializer=lambda x: torch.nn.init.constant_(x, weight), 
bias_initializer=lambda x: torch.nn.init.constant_(x, bias)).to(device)

# Transposed convolution not yet tested
convT = ConvTransposeNd(inChans, outChans, 3, ks, stride, padding, 
kernel_initializer=lambda x: torch.nn.init.constant_(x, weight), 
bias_initializer=lambda x: torch.nn.init.constant_(x, bias)).to(device)

# Create 3D gt convolutions
convGT = nn.Conv3d(inChans, outChans, ks, stride, padding=padding, bias=True, padding_mode=padding_mode)
torch.nn.init.constant_(convGT.weight, weight)
torch.nn.init.constant_(convGT.bias, bias).to(device)
# Transposed
convGTT = nn.ConvTranspose3d(inChans, outChans, ks, stride, padding=padding, padding_mode=padding_mode)
torch.nn.init.constant_(convGTT.weight, weight)
torch.nn.init.constant_(convGTT.bias, bias).to(device)

convGT = convGT.to(device)
convGTT = convGTT.to(device)


# Run timers to compare with torch implementations
start = torch.cuda.Event(enable_timing=True)
end = torch.cuda.Event(enable_timing=True)
print(' ')

# Convolve with ConvNd
torch.cuda.synchronize()
start.record()
out = conv(x)
end.record()
torch.cuda.synchronize()
print("ConvNd time: " + str(start.elapsed_time(end)))

start.record()
outGT = convGT(x)
end.record()
torch.cuda.synchronize()
print("ConvGT time: " + str(start.elapsed_time(end)))

diff = abs(out-outGT)
print("convND error: " + str((torch.sum(diff)/outGT.sum()).item()) + "%",end='\n\n')

# Convolve with ConvTransposeNd
torch.cuda.synchronize()
start.record()
outT = convT(x)
end.record()
torch.cuda.synchronize()
print("ConvTransposeNd time: " + str(start.elapsed_time(end)))

start.record()
outGTT = convGTT(x)
end.record()
torch.cuda.synchronize()
print("ConvTransposeGT time: " + str(start.elapsed_time(end)))


diff = (outT-outGTT)
print("convTransposeND error: " + str((torch.sum(diff)/outGTT.sum()).item()) + "%")


plt.figure(1)
plt.subplot(221)
plt.imshow(x[0,0,:,:,:].sum(2).cpu().data.detach())
plt.title('input')
plt.subplot(222)
plt.imshow(outT[0,:,:,:,:].sum(2).sum(1).cpu().data.detach())
plt.title('convND out')
plt.subplot(223)
plt.imshow(outGTT[0,:,:,:,:].sum(2).sum(1).cpu().data.detach())
plt.title('GT out')
plt.subplot(224)
plt.imshow(diff[0,:,:,:,:].sum(2).sum(1).cpu().data.detach())
plt.title('diff out')
plt.show()