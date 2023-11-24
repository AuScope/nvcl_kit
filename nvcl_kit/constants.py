"""
This module contains a class of scalar constants
"""
from enum import Enum
from typing import Union

class Scalar(str, Enum):  # pragma: no cover
    """
    Enum class of NVCL Scalars, used as input into functions

    The names of scalar classes have 3 parts; first part is class grouping type, second is the TSA mineral matching technique, third part is wavelength:
     1. Min1,2,3 = 1st, 2nd, 3rd most common mineral type OR Grp1,2,3 = 1st, 2nd, 3rd most common group of minerals
     2. uTSA - user, dTSA - domaining, sTSA = system
     3. V = visible light, S = shortwave IR, T = thermal IR, also known as LWIR (long wavelength infrared)

    Source of most class names: "National Virtual Core Scalars":
     http://vocabs.ardc.edu.au/repository/api/lda/csiro/national-virtual-core-library-scalars/v0-3/concept.html


    'sjCLST' is 'System justified constrained least squares'
    'ujCLST' is 'User justified constrained least squares'

    References:

    - [Chart](https://drillhole.pir.sa.gov.au/Resources/ISM62.pdf) courtesy of Geological Survey of South Australia (GSSA) 

    Schodlok, MC, Whitbourn, L, Huntington, J, Mason, P, Green, A, Berman, M, Coward, D, Connor, P,
    Wright, W, Jolivet, M and Martinez, R 2016, HyLogger-3, a visible to shortwave and thermal
    infrared reflectance spectrometer system for drill core logging: functional description:
    Australian Journal of Earth Sciences, v. 63, no. 8, p. 929-940, doi:10.1080/08120099.2016.1231133

    """
    ANY = "*"
    Bound_Water_dTSAS = "Bound_Water dTSAS"
    Bound_Water_sTSAS = "Bound_Water sTSAS"
    Bound_Water_uTSAS = "Bound_Water uTSAS"
    Error_dTSAS = "Error dTSAS"
    Error_dTSAT = "Error dTSAT"
    Error_dTSAV = "Error dTSAV"
    Error_sjCLST = "Error sjCLST"
    Error_sTSAS = "Error sTSAS"
    Error_sTSAT = "Error sTSAT"
    Error_sTSAV = "Error sTSAV"
    Error_ujCLST = "Error ujCLST"
    Error_uTSAS = "Error uTSAS"
    Error_uTSAT = "Error uTSAT"
    Error_uTSAV = "Error uTSAV"
    Grp1_dTSAS = "Grp1 dTSAS"
    Grp1_dTSAT = "Grp1 dTSAT"
    Grp1_dTSAV = "Grp1 dTSAV"
    Grp1_sjCLST = "Grp1 sjCLST"
    Grp1_sTSAS = "Grp1 sTSAS"
    Grp1_sTSAT = "Grp1 sTSAT"
    Grp1_sTSAV = "Grp1 sTSAV"
    Grp1_ujCLST = "Grp1 ujCLST"
    Grp1_uTSAS = "Grp1 uTSAS"
    Grp1_uTSAT = "Grp1 uTSAT"
    Grp1_uTSAV = "Grp1 uTSAV"
    Grp2_dTSAS = "Grp2 dTSAS"
    Grp2_dTSAT = "Grp2 dTSAT"
    Grp2_dTSAV = "Grp2 dTSAV"
    Grp2_sjCLST = "Grp2 sjCLST"
    Grp2_sTSAS = "Grp2 sTSAS"
    Grp2_sTSAT = "Grp2 sTSAT"
    Grp2_sTSAV = "Grp2 sTSAV"
    Grp2_ujCLST = "Grp2 ujCLST"
    Grp2_uTSAS = "Grp2 uTSAS"
    Grp2_uTSAT = "Grp2 uTSAT"
    Grp2_uTSAV = "Grp2 uTSAV"
    Grp3_dTSAT = "Grp3 dTSAT"
    Grp3_sjCLST = "Grp3 sjCLST"
    Grp3_sTSAT = "Grp3 sTSAT"
    Grp3_ujCLST = "Grp3 ujCLST"
    Grp3_uTSAT = "Grp3 uTSAT"
    Min1_dTSAS = "Min1 dTSAS"
    Min1_dTSAT = "Min1 dTSAT"
    Min1_dTSAV = "Min1 dTSAV"
    Min1_sjCLST = "Min1 sjCLST"
    Min1_sTSAS = "Min1 sTSAS"
    Min1_sTSAV = "Min1 sTSAV"
    Min1_ujCLST = "Min1 ujCLST"
    Min1_uTSAS = "Min1 uTSAS"
    Min1_uTSAT = "Min1 uTSAT"
    Min1_uTSAV = "Min1 uTSAV"
    Min2_dTSAS = "Min2 dTSAS"
    Min2_dTSAT = "Min2 dTSAT"
    Min2_dTSAV = "Min2 dTSAV"
    Min2_sjCLST = "Min2 sjCLST"
    Min2_sTSAS = "Min2 sTSAS"
    Min2_sTSAT = "Min2 sTSAT"
    Min2_sTSAV = "Min2 sTSAV"
    Min2_ujCLST = "Min2 ujCLST"
    Min2_uTSAS = "Min2 uTSAS"
    Min2_uTSAT = "Min2 uTSAT"
    Min2_uTSAV = "Min2 uTSAV"
    Min3_dTSAT = "Min3 dTSAT"
    Min3_sjCLST = "Min3 sjCLST"
    Min3_sTSAT = "Min3 sTSAT"
    Min3_ujCLST = "Min3 ujCLST"
    Min3_uTSAT = "Min3 uTSAT"
    NIL_Stat_dTSAS = "NIL_Stat dTSAS"
    NIL_Stat_dTSAT = "NIL_Stat dTSAT"
    NIL_Stat_dTSAV = "NIL_Stat dTSAV"
    NIL_Stat_sTSAS = "NIL_Stat sTSAS"
    NIL_Stat_sTSAT = "NIL_Stat sTSAT"
    NIL_Stat_sTSAV = "NIL_Stat sTSAV"
    NIL_Stat_uTSAS = "NIL_Stat uTSAS"
    NIL_Stat_uTSAT = "NIL_Stat uTSAT"
    NIL_Stat_uTSAV = "NIL_Stat uTSAV"
    SNR_dTSAS = "SNR dTSAS"
    SNR_dTSAT = "SNR dTSAT"
    SNR_dTSAV = "SNR dTSAV"
    SNR_sTSAS = "SNR sTSAS"
    SNR_sTSAT = "SNR sTSAT"
    SNR_sTSAV = "SNR sTSAV"
    SNR_uTSAS = "SNR uTSAS"
    SNR_uTSAT = "SNR uTSAT"
    SNR_uTSAV = "SNR uTSAV"
    TirBkgOffset = "TirBkgOffset"
    TirDeltaTemp = "TirDeltaTemp"
    TIR_Results = "TIR Results"
    TSA_S_Water = "TSA_S Water"
    TSA_V_Water = "TSA_V Water"
    Unbound_Water_dTSAS = "Unbound_Water dTSAS"
    Unbound_Water_sTSAS = "Unbound_Water sTSAS"
    Unbound_Water_uTSAS = "Unbound_Water uTSAS"
    Wt1_dTSAS = "Wt1 dTSAS"
    Wt1_dTSAT = "Wt2 sTSAT"
    Wt1_dTSAV = "Wt1 dTSAV"
    Wt1_sjCLST = "Wt1 sjCLST"
    Wt1_sTSAS = "Wt1 sTSAS"
    Wt1_sTSAT = "Wt1 uTSAT"
    Wt1_sTSAV = "Wt1 sTSAV"
    Wt1_ujCLST = "Wt1 ujCLST"
    Wt1_uTSAS = "Wt1 uTSAS"
    Wt1_uTSAV = "Wt1 uTSAV"
    Wt2_dTSAS = "Wt2 dTSAS"
    Wt2_dTSAV = "Wt2 dTSAV"
    Wt2_sjCLST = "Wt2 sjCLST"
    Wt2_sTSAS = "Wt2 sTSAS"
    Wt2_sTSAV = "Wt2 sTSAV"
    Wt2_ujCLST = "Wt2 ujCLST"
    Wt2_uTSAS = "Wt2 uTSAS"
    Wt2_uTSAT = "Wt2 dTSAT"
    Wt2_uTSAV = "Wt2 uTSAV"
    Wt3_dTSAT = "Min1 sTSAT"
    Wt3_sjCLST = "Wt3 sjCLST"
    Wt3_sTSAT = "Wt3 uTSAT"
    Wt3_ujCLST = "Wt3 ujCLST"

def has_tsa(scalar: Union[Scalar,str]) -> bool:
    ''' Does this scalar indicate a TSA ('The Spectral Assistant') algorithm ?

    :param scalar: a scalar in the form of either a string or a 'Scalar' object
    :return: True iff scalar indicates TSA
    '''
    return str(scalar)[-4:-1] == 'TSA'

def has_cls(scalar: Union[Scalar,str]) -> bool:
    ''' Does this scalar indicate a Constrained Least Squares (CLS) algorithm ?

    :param scalar: a scalar in the form of either a string or a 'Scalar' object
    :return: True iff scalar indicates CLS 
    '''
    return str(scalar)[-4:-1] == 'CLS'

def has_VNIR(scalar: Union[Scalar,str]) -> bool:
    ''' Does this scalar indicate visible and near-infrared (VNIR) wavelengths ?

    :param scalar: a scalar in the form of either a string or a 'Scalar' object
    :return: True iff scalar indicates VNIR
    '''
    return (has_tsa(scalar) or has_cls(scalar)) and str(scalar)[-1] == 'V'

def has_SWIR(scalar: Union[Scalar,str]) -> bool:
    ''' Does this scalar indicate short-wavelength infrared (SWIR) wavelengths ?

    :param scalar: a scalar in the form of either a string or a 'Scalar' object
    :return: True iff scalar indicates SWIR 
    '''
    return (has_tsa(scalar) or has_cls(scalar)) and str(scalar)[-1] == 'S'

def has_TIR(scalar: Union[Scalar,str]) -> bool:
    ''' Does this scalar indicate thermal infrared wavelengths (TIR) ?

    :param scalar: a scalar in the form of either a string or a 'Scalar' object
    :return: True iff scalar indicates TIR
    '''
    return (has_tsa(scalar) or has_cls(scalar)) and str(scalar)[-1] == 'T'

