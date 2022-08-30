## Python notebooks demonstrating NVCL_KIT

**NB:** These notebooks assume user has already installed:

- nvcl_kit
- matplotlib
- xmltodict
- pandas

### Installation tips

1. Some free online notebooks do not permit installation of additional packages. These platforms cannot be used for running NVCL_KIT notebooks

2. If your notebook allows it, you can install packages from a cell:

```
import sys
!{sys.executable} -m pip install nvcl_kit matplotlib xmltodict pandas
```

3. If you get an error from the above, then try installing a new kernel:

1) File -> New -> Notebook
2) Select "Python 3" kernel, click "Select"
3) Goto [install_nvcl_kit.sh](https://gitlab.com/csiro-geoanalytics/python-shared/nvcl_kit/-/blob/master/notebooks/install_nvcl_kit.sh)
copy text, paste into first cell
4) Hit arrow to execute 
5) Once "[*]" has become a "[1]", you can open an nvcl_kit notebook, change to the kernel to "NVCL KIT" and run it

*NB:* The script in Step 3 is for Python 3.8, if you use a different version of Python please modify accordingly 

