#!/usr/bin/env python3

def autodetect_election_cols(columns, include_cvap = False):
    """
    Attempt to autodetect election cols from a given list
    """
    partial_cols = ["SEN", "PRES", "GOV", "TRE", "AG", "LTGOV", "AUD", "USH", "SOS", "CAF", "SSEN", "STH", "TOTVOTE", "RGOV", "DGOV", "DPRES", "RPRES", "DSC", "RSC", "EL", "G16", "G17", "G18", "G20", "COMP", "ATG", "SH", "SP_SEN", "USS", "SOC", "BOSMAY", "SS08P", "SS13P"]
    if include_cvap:
        election_cols = [x for x in columns if any([x.startswith(y) or "CVAP" in x for y in partial_cols])]
    else:
        election_cols = [x for x in columns if any([x.startswith(y) for y in partial_cols])]

    if "SEND" in election_cols:
        del election_cols[election_cols.index("SEND")]
    if "SENDIST" in election_cols:
        del election_cols[election_cols.index("SENDIST")]

    return election_cols
