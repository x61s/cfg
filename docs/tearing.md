# Enable TearFree with AMD cards

Create `/etc/X11/xorg.conf.d/20-amdgpu.conf` configuration file with this content:

```
Section "Device"
     Identifier "AMD"
     Driver "amdgpu"
     Option "TearFree" "true"
EndSection
```

Restart X. Enjoy.

