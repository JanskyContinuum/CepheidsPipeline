# CepheidsPipeline: Multi-Band Photometric Analysis & P-L Relation

An automated, modular Python pipeline for processing astronomical time-series data of Classical Cepheids. This tool extracts raw photometric measurements, performs digital signal processing to determine pulsation periods, and constructs empirical Period-Luminosity (Leavitt Law) relations across multiple photometric filters (V, I) and reddening-free Wesenheit indices.

## Data Source: The OGLE Survey
The pipeline fetches raw photometry of Cepheids in the Large Magellanic Cloud (LMC) sourced from the **Optical Gravitational Lensing Experiment (OGLE-IV)**, operated by the University of Warsaw.

## Astronomical Physics & The P-L Relation

When analyzing Period-Luminosity relations, different photometric bands exhibit different levels of scatter around the regression line:

### 1. Intrinsic Scatter and Passbands
The scatter in the optical P-L relation (such as in the V and I bands) is not strictly instrumental error. It arises primarily from the finite temperature width of the Cepheid **Instability Strip** on the Hertzsprung-Russell diagram. A Cepheid of a given pulsation period can have a slightly different temperature (and thus color), changing its absolute magnitude. The V-band is highly sensitive to temperature changes, leading to significant intrinsic scatter. The I-band is further to the red and is therefore less affected by this temperature width, reducing the intrinsic scatter.

### 2. Extinction and Near-Infrared (NIR)
Interstellar dust absorbs and scatters shorter wavelengths of light more efficiently than longer ones (extinction). This physically dims and reddens starlight. Because $A_\lambda \propto \lambda^{-1.6}$, Near-Infrared (NIR) passbands (like J, H, K) are vastly less susceptible to interstellar extinction compared to optical bands. In future implementations, adding J/H/K bands to this pipeline will yield extremely tight P-L relations.

### 3. The Wesenheit Index
To bypass the problem of unknown interstellar extinction in optical bands, astronomers use the **Wesenheit Index ($W$)**. It is defined as a linear combination of a magnitude and a color index, utilizing a fixed standard extinction law (e.g., $R_I = 1.55$ for LMC $V, I$ data). 
Formula: $W_I = I - R_I \times (V - I)$
By definition, the Wesenheit function is an extinction-free pseudo-magnitude. When plotted against $\log(P)$, it naturally removes interstellar reddening and strongly mitigates the Instability Strip temperature width effect, resulting in a dramatically reduced scatter in the $W_I$ P-L relation.

## Quick Start

### 1. Installation
```bash
git clone [https://github.com/JanskyContinuum/CepheidsPipeline.git](https://github.com/JanskyContinuum/CepheidsPipeline.git)
cd CepheidsPipeline
pip install -r requirements.txt
```

### 2. Single Star Analysis
To run the pipeline for a single star and generate a diagnostic multi-panel plot (raw data, periodogram, and phase-folded light curve):
```bash
python scripts/analyze_cepheid.py 1
```
(This analyzes OGLE-LMC-CEP-0001. You can replace 1 with any catalog number).

### 3. Batch Processing (Period-Luminosity Relation)
To process a sample of Cepheids in V and I bands, calculate Wesenheit indices, and generate the regression analysis:
```bash
python scripts/build_pl_relation.py
```

## 📈 Results & Interpretation
The pipeline generates analytical plots and CSV datasets, automatically saved in the results/ directory. You can view sample outputs in the results/examples/ folder.

### 1. Phase-Folded Light Curves
The single-star analysis collapses years of chaotic, irregularly sampled observations into a clean, normalized pulsation phase [0.0, 2.0], revealing the true physical waveform (e.g., the characteristic asymmetrical "shark fin" of fundamental mode Cepheids).

<p align="center">
  <img src="results/examples/OGLE-LMC-CEP-0001_analysis.png" alt="Light Curve of OGLE-LMC-CEP-0001" width="650">
  <br>
  <em>Light Curve of OGLE-LMC-CEP-0001</em>
</p>

### 2. Multi-Band Period-Luminosity Relation & Wesenheit Index

When running the batch analysis (`build_pl_relation.py`), the pipeline outputs a 3-panel scatter plot comparing the Period-Luminosity (Leavitt Law) relation across the V band, I band, and the reddening-free Wesenheit Index ($W_I$).

<p align="center">
  <img src="results/examples/pl_relation_multiband_scatter.png" alt="Multi-Band Period-Luminosity relation for LMC Cepheids" width="850">
  <br>
  <em>Comparison of the Leavitt Law across V, I, and Wesenheit indices, showing the progressive reduction in statistical scatter.</em>
</p>

The multi-band regression fits and scatter values captured by the pipeline are:
* **V-band:** $m = -2.344 \cdot \log_{10}(P) + 17.056$ (Scatter RMS: $0.326\text{ mag}$)
* **I-band:** $m = -2.548 \cdot \log_{10}(P) + 16.436$ (Scatter RMS: $0.284\text{ mag}$)
* **Wesenheit Index ($W_I$):** $m = -2.864 \cdot \log_{10}(P) + 15.474$ (Scatter RMS: $0.250\text{ mag}$)

As demonstrated by the decreasing RMS scatter values, moving from the optical V-band to the I-band, and finally to the extinction-corrected Wesenheit index $W_I$, significantly tightens the relations.