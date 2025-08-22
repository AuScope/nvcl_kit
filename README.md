# nvcl_kit: Access AuScope National Virtual Core Library (NVCL) data services

[![nvcl_kit build, test, pages](https://github.com/AuScope/nvcl_kit/actions/workflows/nvcl_kit.yml/badge.svg)](https://github.com/AuScope/nvcl_kit/actions/workflows/nvcl_kit.yml)

[![pdm-managed](https://img.shields.io/badge/pdm-managed-blueviolet)](https://pdm.fming.dev)

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/AuScope/nvcl_kit/HEAD)



## Introduction

**nvcl_kit** is a Python package that provides access to Australia's NVCL (National Virtual Core Library). This is a national database of drill cores that have been analysed by the CSIRO-developed HyLogger hyperspectral core-scanning system. The Hylogger system uses visible and near-infrared, shortwave and thermal infrared reflectance spectroscopy and automatic mineralogical analysis to extract mineralogy data from each drill core.

The mineralogy data is maintained by Australia's State and Territory geological surveys and can be accessed via publicly available web services. **nvcl_kit** combines these services with OCG WFS borehole data to provide a complete picture of each borehole. It is designed to shield the user from the arcane details of how to establish connections, retrieve and combine datasets.

**nvcl_kit** has two layers of API. The first layer is designed to make it quick and easy to access the borehole mineralogy. The second layer is for more expert users providing access to the full range of available data products. 

#### More Information

[AuScope NVCL - Australia’s mineralogy database](https://www.auscope.org.au/nvcl)  

[Hylogger-3](https://research.csiro.au/drill-core-lab/hylogger-3/)


## How to use it

1. A brief API tutorial is [here](https://github.com/AuScope/nvcl_kit/blob/master/introduction.rst)
2. Example Jupyter Notebooks are available to try, open this [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/AuScope/nvcl_kit/HEAD) and go to "notebooks" folder
3. There is a rough demonstration script [here](https://github.com/AuScope/nvcl_kit/blob/master/demo.py)
4. API documentation can be found [here](https://auscope.github.io/nvcl_kit)


## License

**nvcl_kit** is available under [CSIRO Open Source Software Licence Agreement](LICENSE) (variation of the BSD / MIT License)

## Citation

If you use this package in your research please cite:

Fazio, Vincent; Mule, Shane; Hunt, Alex; Jiang, Lingbo; Warren, Peter; Selvaraju, Venkataramanan (2024): nvcl_kit: Access AuScope National Virtual Core Library (NVCL) data services. v6. CSIRO. Service Collection. http://hdl.handle.net/102.100.100/480016?index=1
