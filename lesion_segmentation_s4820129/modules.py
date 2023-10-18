import torch
from torch import nn

class ImprovedUNET(nn.Module):
  def __init__(self, n_channels, n_classes):
    super(ImprovedUNET, self).__init__()
    #first level down
    self._n_to_16_d = nn.Conv2d(n_channels, 16, kernel_size=3, stride=1, padding=1)
    self._16_to_16_d = self.context_block(16, 16)
    #second layer down
    self._16_to_32_d = self.stride_layer(16, 32)
    self._32_to_32_d = self.context_block(32,32)
    #third layer down
    self._32_to_64_d = self.stride_layer(32, 64)
    self._64_to_64_d = self.context_block(64, 64)
    #fourth layer down
    self._64_to_128_d = self.stride_layer(64, 128)
    self._128_to_128_d = self.context_block(128, 128)
    #fifth layer down
    self._128_to_256_b = self.stride_layer(128, 256)
    self._256_to_256_b = self.context_block(256, 256)
    self._256_to_128_b = self.upsampling_block(256, 128)
    #fourth layer up
    self.c1_to_128_u = self.localization_block(256, 128)
    self._128_to_64_u = self.upsampling_block(128, 64)
    #third layer up
    self.c2_to_64_u = self.localization_block(128, 64)
    self._64_to_32_u = self.upsampling_block(64, 32)
    #second layer up
    self.c3_to_32_u = self.localization_block(64, 32)
    self._32_to_16_u = self.upsampling_block(32, 16)
    #first layer up
    self.c4_to_32_u = nn.Conv2d(32, 32, kernel_size=3, padding=1, stride=1)
    self.softmax = nn.Softmax(dim=1)
    
    ##segmentation
    self.segmentation1 = nn.Conv2d(64, 32, kernel_size=3, padding=1)
    self.segmentation2 = nn.Conv2d(32, 16, kernel_size=3, padding=1)
    self.segmentation3 = nn.Conv2d(32, 1, kernel_size=3, padding=1)
    self.scale1 = self.upsampling_block(32, 16,2)
    self.scale2 = self.upsampling_block(16,1,2,1,0)


  def context_block(self, in_channels, out_channels):
    return nn.Sequential(
        
        nn.InstanceNorm2d(in_channels),
        nn.LeakyReLU(negative_slope=0.01, inplace=True),
        nn.Conv2d(in_channels, out_channels, kernel_size=3, stride=1, padding=1),

        nn.Dropout2d(p=0.3),

        nn.InstanceNorm2d(in_channels),
        nn.LeakyReLU(negative_slope=0.01, inplace=True),
        nn.Conv2d(out_channels, out_channels, kernel_size=3, stride=1, padding=1),
    )

  def stride_layer(self, in_channels, out_channels):
    return nn.Sequential(
        nn.Conv2d(in_channels, out_channels, kernel_size=3, stride=2, padding=1)
    )

  def localization_block(self, in_channels, out_channels):
    return nn.Sequential(
        nn.Conv2d(in_channels, out_channels, kernel_size=3, stride=1, padding=1),
        nn.LeakyReLU(negative_slope=0.01, inplace=True),
        nn.Conv2d(out_channels, out_channels, kernel_size=1, stride=1, padding=0),
        nn.LeakyReLU(negative_slope=0.01, inplace=True),
    )

  def upsampling_block(self, in_channels, out_channels, scale_factor=2,kernel_size=3,padding=1):
    return nn.Sequential(
        nn.Upsample(scale_factor=scale_factor, mode='nearest'),
        nn.Conv2d(in_channels, out_channels, kernel_size=kernel_size, padding=padding)
    )

  
  def forward(self, x):
    #down
    x = self._n_to_16_d(x)
    r1 = x + self._16_to_16_d(x)

    x = self._16_to_32_d(r1)
    r2 = x + self._32_to_32_d(x)

    x = self._32_to_64_d(r2)
    r3 = x + self._64_to_64_d(x)

    x = self._64_to_128_d(r3)
    r4 = x + self._128_to_128_d(x)
    
    #bottom
    x = self._128_to_256_b(r4)
    x = x + self._256_to_256_b(x)
    x = self._256_to_128_b(x)

    #up
    x = torch.cat([x,r4],dim=1) #c1
    x = self.c1_to_128_u(x)
    x = self._128_to_64_u(x)
    x = torch.cat([x,r3],dim=1)
    s1 = self.c2_to_64_u(x)
    x = self._64_to_32_u(s1)
    
    s1 = self.segmentation1(s1)
    s1 = self.scale1(s1)

    x = torch.cat([x,r2],dim=1)
    s2 = self.c3_to_32_u(x)
    x = self._32_to_16_u(s2)

    s2 = self.segmentation2(s2)
    s2 += s1
    s2 = self.scale2(s2)

    x = torch.cat([x,r1],dim=1)
    x = self.c4_to_32_u(x)
    
    x = s2 + self.segmentation3(x)

    return x