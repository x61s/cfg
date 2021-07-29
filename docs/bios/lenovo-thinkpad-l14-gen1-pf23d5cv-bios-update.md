# Lenovo Thinkpad L14 Gen1 BIOS Update

MTM: 20U5-001XTX

S/N: PF23D5CV

Download Lenovo BIOS Bootable CD for your Laptop model from [official website](https://pcsupport.lenovo.com/tr/en/products/laptops-and-netbooks/thinkpad-l-series-laptops/thinkpad-l14-type-20u5-20u6/downloads/driver-list/component?name=BIOS%2FUEFI).

Install El Torito image extract utility.

```
# emerge -av geteltorito
```

Extract El Torito image from Bootable CD ISO image to *update.img* file.

```
$ geteltorito -o ./update.img ./r19ur09w.iso
```

Write *update.img* to USB stick with dd utility.

```
# dd if=update.img of=/dev/sdX bs=64K status=progress
```

Use this USB stick to boot your laptop and carefully read further instructions.

