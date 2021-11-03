"""
This module contains a class of scalar constants
"""
from enum import Enum


class Scalar(str, Enum): # pragma: no cover
    """
    Enum class of NVCL Scalars, used as input into functions

    The names of scalar classes have 3 parts; first part is class grouping type, second is the TSA mineral matching technique, third part is wavelength:
     1. Min1,2,3 = 1st, 2nd, 3rd most common mineral type OR Grp1,2,3 = 1st, 2nd, 3rd most common group of minerals
     2. uTSA - user, dTSA - domaining, sTSA = system
     3. V = visible light, S = shortwave IR, T = thermal IR

    Source of names: "National Virtual Core Scalars": http://vocabs.ardc.edu.au/repository/api/lda/csiro/national-virtual-core-library-scalars/v0-3/concept.html

    """
    ANY = "*";
    TSA_S_Water = "TSA_S Water";
    Bound_Water_sTSAS = "Bound_Water sTSAS";
    Bound_Water_uTSAS = "Bound_Water uTSAS";
    Bound_Water_dTSAS = "Bound_Water dTSAS";
    Error_sTSAS = "Error sTSAS";
    Error_uTSAS = "Error uTSAS";
    Error_dTSAS = "Error dTSAS";
    NIL_Stat_sTSAS = "NIL_Stat sTSAS";
    NIL_Stat_uTSAS = "NIL_Stat uTSAS";
    NIL_Stat_dTSAS = "NIL_Stat dTSAS";
    SNR_sTSAS = "SNR sTSAS";
    SNR_uTSAS = "SNR uTSAS";
    SNR_dTSAS = "SNR dTSAS";
    Unbound_Water_sTSAS = "Unbound_Water sTSAS";
    Unbound_Water_uTSAS = "Unbound_Water uTSAS";
    Unbound_Water_dTSAS = "Unbound_Water dTSAS";
    Wt1_sTSAS = "Wt1 sTSAS";
    Wt1_uTSAS = "Wt1 uTSAS";
    Wt1_dTSAS = "Wt1 dTSAS";
    Wt2_sTSAS = "Wt2 sTSAS";
    Wt2_uTSAS = "Wt2 uTSAS";
    Wt2_dTSAS = "Wt2 dTSAS";
    Min1_sTSAS = "Min1 sTSAS";
    Min1_uTSAS = "Min1 uTSAS";
    Min1_dTSAS = "Min1 dTSAS";
    Min2_sTSAS = "Min2 sTSAS";
    Min2_uTSAS = "Min2 uTSAS";
    Min2_dTSAS = "Min2 dTSAS";
    Grp1_sTSAS = "Grp1 sTSAS";
    Grp1_uTSAS = "Grp1 uTSAS";
    Grp1_dTSAS = "Grp1 dTSAS";
    Grp2_sTSAS = "Grp2 sTSAS";
    Grp2_uTSAS = "Grp2 uTSAS";
    Grp2_dTSAS = "Grp2 dTSAS";
    TSA_V_Water = "TSA_V Water";
    Error_sTSAV = "Error sTSAV";
    Error_uTSAV = "Error uTSAV";
    Error_dTSAV = "Error dTSAV";
    NIL_Stat_sTSAV = "NIL_Stat sTSAV";
    NIL_Stat_uTSAV = "NIL_Stat uTSAV";
    NIL_Stat_dTSAV = "NIL_Stat dTSAV";
    SNR_sTSAV = "SNR sTSAV";
    SNR_uTSAV = "SNR uTSAV";
    SNR_dTSAV = "SNR dTSAV";
    Wt1_sTSAV = "Wt1 sTSAV";
    Wt1_uTSAV = "Wt1 uTSAV";
    Wt1_dTSAV = "Wt1 dTSAV";
    Wt2_sTSAV = "Wt2 sTSAV";
    Wt2_uTSAV = "Wt2 uTSAV";
    Wt2_dTSAV = "Wt2 dTSAV";
    Min1_sTSAV = "Min1 sTSAV";
    Min1_uTSAV = "Min1 uTSAV";
    Min1_dTSAV = "Min1 dTSAV";
    Min2_sTSAV = "Min2 sTSAV";
    Min2_uTSAV = "Min2 uTSAV";
    Min2_dTSAV = "Min2 dTSAV";
    Grp1_sTSAV = "Grp1 sTSAV";
    Grp1_uTSAV = "Grp1 uTSAV";
    Grp1_dTSAV = "Grp1 dTSAV";
    Grp2_sTSAV = "Grp2 sTSAV";
    Grp2_uTSAV = "Grp2 uTSAV";
    Grp2_dTSAV = "Grp2 dTSAV";
    TIR_Results = "TIR Results";
    Error_sTSAT = "Error sTSAT";
    Error_uTSAT = "Error uTSAT";
    Error_dTSAT = "Error dTSAT";
    NIL_Stat_sTSAT = "NIL_Stat sTSAT";
    NIL_Stat_uTSAT = "NIL_Stat uTSAT";
    NIL_Stat_dTSAT = "NIL_Stat dTSAT";
    SNR_sTSAT = "SNR sTSAT";
    SNR_uTSAT = "SNR uTSAT";
    SNR_dTSAT = "SNR dTSAT";
    Wt1_sTSAT = "Wt1 uTSAT";
    Wt1_dTSAT = "Wt2 sTSAT";
    Wt2_uTSAT = "Wt2 dTSAT";
    Wt3_sTSAT = "Wt3 uTSAT";
    Wt3_dTSAT = "Min1 sTSAT";
    Min1_uTSAT = "Min1 uTSAT";
    Min1_dTSAT = "Min1 dTSAT";
    Min2_sTSAT = "Min2 sTSAT";
    Min2_uTSAT = "Min2 uTSAT";
    Min2_dTSAT = "Min2 dTSAT";
    Min3_sTSAT = "Min3 sTSAT";
    Min3_uTSAT = "Min3 uTSAT";
    Min3_dTSAT = "Min3 dTSAT";
    Grp1_sTSAT = "Grp1 sTSAT";
    Grp1_uTSAT = "Grp1 uTSAT";
    Grp1_dTSAT = "Grp1 dTSAT";
    Grp2_sTSAT = "Grp2 sTSAT";
    Grp2_uTSAT = "Grp2 uTSAT";
    Grp2_dTSAT = "Grp2 dTSAT";
    Grp3_sTSAT = "Grp3 sTSAT";
    Grp3_uTSAT = "Grp3 uTSAT";
    Grp3_dTSAT = "Grp3 dTSAT";
    TirBkgOffset = "TirBkgOffset";
    TirDeltaTemp = "TirDeltaTemp";
