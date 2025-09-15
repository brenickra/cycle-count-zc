"""
file_io.py

Handles reading of Lynx-format time-series files (.TEM, .LTX, .LTD)
and text-based files (.csv, .txt, .asc).
"""

import os
import re
import numpy as np
import pandas as pd
import win32com.client

# ==============================
# Section: Dispatcher Function
# ==============================
def read_file_data(filename):
    """
    Reads time-series data and metadata from supported file types.

    Parameters
    ----------
    filename : str
        Path to the file.

    Returns
    -------
    df_temp : pd.DataFrame
        DataFrame with all channels and time.
    base : str
        Filename without extension.
    duration : list of float
        Duration of signal in seconds.
    nomes_sinais : list of str
        Channel names including time.
    Fs : float
        Sampling frequency (Hz).
    """
    ext = os.path.splitext(filename)[1].lower()

    if ext in [".tem", ".ltx", ".ltd"]:
        return read_lynx_file(filename)
    elif ext in [".csv", ".txt", ".asc"]:
        return read_text_file(filename)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

# ==============================
# Section: Lynx Binary File Reader
# ==============================
def read_lynx_file(filename):
    """
    Reads a time-series file using the Lynx COM interface and returns
    the signal data along with metadata.

    Parameters:
    ----------
    filename : str
        Path to the file to be read.

    Returns:
    -------
    df_temp : pd.DataFrame
        DataFrame containing all channels and the time vector.
    base : str
        Filename without extension.
    duration : list of float
        Duration of the signal in seconds.
    nomes_sinais : list of str
        Names of all channels, including time.
    Fs : float
        Sampling frequency (Hz).
    """
    oFileTS = win32com.client.Dispatch("LynxFile.FileTS")
    base = os.path.splitext(filename)[0]

    # Abrir arquivo
    if not oFileTS.OpenFile(filename):
        raise RuntimeError(f"Erro ao abrir arquivo: {oFileTS.ErrorCodeStr}")

    # Metadados
    name = oFileTS.SnName
    unit = oFileTS.SnUnit
    channels = oFileTS.nChannels
    length = oFileTS.nSamples
    Fs = oFileTS.SampleFreq

    # Pré-alocação
    data_matrix = []
    channel_names = []

    for i in range(channels):
        # Nome + unidade
        '''r = name(i).replace(" ", "_")
        u = unit(i).replace(" ", "_")
        r_with_unit = f"{r}[{u}]" if u else r'''

        ###########################################################################
        # Limpa espaços, tabs e normaliza nome
        r = re.sub(r'\s+', '_', name(i).strip())
        u = re.sub(r'\s+', '_', unit(i).strip())

        # Remove caracteres não alfanuméricos indesejados, exceto "_", "-", "." e "/"
        r = re.sub(r'[^\w\-./]', '', r)
        u = re.sub(r'[^\w\-./]', '', u)

        # Formata nome com unidade
        r_with_unit = f"{r}[{u}]" if u else r
        r_with_unit = f"{i+1}:{r_with_unit}"
        ###########################################################################
        
        # Buffer inicial
        buffer = np.zeros(length, dtype=np.float64)
        result = oFileTS.ReadBuffer(i, 0, length, buffer)
        
        # Tratar retorno: pode vir tupla (success, buffer, NOut)
        if isinstance(result, tuple):
            success, buffer_data, n_out = result
        else:
            raise RuntimeError("ReadBuffer retornou valor inesperado.")

        if not success:
            raise RuntimeError(f"Erro ao ler canal {i}: {oFileTS.ErrorCodeStr}")
        
        data_matrix.append(buffer_data)
        channel_names.append(r_with_unit)

    # Construir DataFrame
    df_temp = pd.DataFrame(np.vstack(data_matrix).T, columns=channel_names)
    #df_temp["time"] = np.arange(0, length / Fs, 1 / Fs)
    df_temp["time"] = np.linspace(0, (length - 1) / Fs, length)

    duration = [length / Fs]
    nomes_sinais = list(df_temp.columns)

    return df_temp, base, duration, nomes_sinais, Fs
    
    '''oFileTS = win32com.client.Dispatch("LynxFile.FileTS")
    base = os.path.splitext(filename)[0]
    
    oFileTS.OpenFile(filename)
    error = oFileTS.ErrorCode
    name = oFileTS.SnName
    channels = oFileTS.nChannels
    unit = oFileTS.SnUnit
    length = oFileTS.nSamples
    Fs = oFileTS.SampleFreq
    
    # Generate time vector
    t = pd.Series(np.arange(0, length / Fs, 1 / Fs), name="time")
    df_temp = pd.DataFrame()
    
    for i in range(channels):
        r = name(i).replace(" ", "_")
        u = unit(i).replace(" ", "_")
        r_with_unit = f"{r}[{u}]" if u else r
        data = oFileTS.ReadBuffer(i, 0, length, np.zeros(length))[1]
        df_temp[r_with_unit] = pd.Series(data, name=r_with_unit)

    df_temp = pd.concat([df_temp, t], axis=1)
    duration = [length / Fs]
    nomes_sinais = list(df_temp.columns)
    
    return df_temp, base, duration, nomes_sinais, Fs'''

# ==============================
# Section: Text File Reader
# ==============================
def read_text_file(filename):
    """
    Reads a text-based time-series file (CSV, TXT, ASC) and returns the DataFrame,
    base name, duration, channel names, and sampling frequency.

    Parameters:
    ----------
    filename : str
        Path to the file.

    Returns:
    -------
    df_temp : pd.DataFrame
        DataFrame with all channels and the time column at the end.
    base : str
        Filename without extension.
    duration : list of float
        Duration of the signal in seconds.
    nomes_sinais : list of str
        List of all channel names, including time at the end.
    Fs : float
        Sampling frequency (Hz), computed from the time column.
    """
    import os
    import pandas as pd

    base = os.path.splitext(os.path.basename(filename))[0]

    # Read the text file, assuming comma separator
    df_temp = pd.read_csv(filename)

    if "time" not in df_temp.columns:
        raise ValueError(f"'time' column not found in {filename}")

    # Move 'time' column to the end if it’s at the start
    if df_temp.columns[0] == "time":
        cols = list(df_temp.columns[1:]) + ["time"]
        df_temp = df_temp[cols]

    # Calculate duration and Fs from 'time' column
    time_data = df_temp["time"]
    length = len(time_data)
    duration = [time_data.iloc[-1] - time_data.iloc[0]]
    Fs = (length - 1) / duration[0] if duration[0] != 0 else 0

    nomes_sinais = list(df_temp.columns)

    return df_temp, base, duration, nomes_sinais, Fs

# ==============================
# Section: Channel Header Reader Dispatcher
# ==============================
def read_channel_headers(filename):
    """
    Quickly retrieves channel names (with units) from file.

    Parameters
    ----------
    filename : str

    Returns
    -------
    List[str]
    """
    ext = os.path.splitext(filename)[1].lower()

    if ext in [".tem", ".ltx", ".ltd"]:
        return read_lynx_headers(filename)
    elif ext in [".csv", ".txt", ".asc"]:
        return read_text_headers(filename)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

# ==============================
# Section: Lynx Header Reader
# ==============================
def read_lynx_headers(filename):
    """
    Quickly retrieves the channel names (with units) from a Lynx-format file,
    without reading full data buffers.

    Parameters
    ----------
    filename : str
        Full path to .TEM, .LTX, or .LTD file.

    Returns
    -------
    List[str]
        List of channel names including units (e.g., 'G_12[MPa]')
    """
    oFileTS = win32com.client.Dispatch("LynxFile.FileTS")
    oFileTS.OpenFile(filename)
    
    name = oFileTS.SnName
    unit = oFileTS.SnUnit
    channels = oFileTS.nChannels

    nomes_sinais = []

    for i in range(channels):
        '''r = name(i).replace(" ", "_")
        u = unit(i).replace(" ", "_")
        r_with_unit = f"{r}[{u}]" if u else r'''
        
        ###########################################################################
        # Limpa espaços, tabs e normaliza nome
        r = re.sub(r'\s+', '_', name(i).strip())
        u = re.sub(r'\s+', '_', unit(i).strip())

        # Remove caracteres não alfanuméricos indesejados, exceto "_", "-", "." e "/"
        r = re.sub(r'[^\w\-./]', '', r)
        u = re.sub(r'[^\w\-./]', '', u)

        # Formata nome com unidade
        r_with_unit = f"{r}[{u}]" if u else r
        r_with_unit = f"{i+1}:{r_with_unit}"
        ###########################################################################       
        
        nomes_sinais.append(r_with_unit)

    return nomes_sinais

# ==============================
# Section: Text Header Reader
# ==============================
def read_text_headers(filename):
    """
    Quickly reads the header line (first line) of a text file and returns the channel names.

    Parameters:
    ----------
    filename : str
        Path to the file.

    Returns:
    -------
    nomes_sinais : list of str
        List of channel names, without 'time'.
    """
    with open(filename, "r") as f:
        header_line = f.readline()

    # Split and strip header names
    nomes_sinais = [x.strip() for x in header_line.strip().split(",")]

    # Remove 'time' from list if present (consistência com Lynx)
    nomes_sinais = [s for s in nomes_sinais if s.lower() != "time"]

    return nomes_sinais
