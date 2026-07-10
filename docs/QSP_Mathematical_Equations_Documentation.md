---
output:
  word_document: default
  html_document: default
---
# Mathematical Equations and Expressions Documentation
## Expanded 19-State QSP Model for ICI-Induced Thyroid Dysfunction

---

## 1. Overview

This document is the complete mathematical specification of the expanded
quantitative systems pharmacology (QSP) model of immune checkpoint inhibitor
(ICI)-induced thyroid dysfunction. It describes exactly the implemented model in
`qsp_expanded/` (state ordering in `parameters.py`, right-hand side in
`ode_system.py`, status classification in `classification.py`, susceptibility
sampling in `population.py`). All outputs are in-silico; no real patient data are
used.

The model is a system of **19 coupled ordinary differential equations (ODEs)**
organized into **five modules**: (1) checkpoint pharmacology, (2) T-cell
dynamics, (3) cytokine network, (4) thyroid gland and signaling, and (5) the
hypothalamic-pituitary-thyroid (HPT) axis.

## 2. State Vector

The 19-state vector $y(t) \in \mathbb{R}^{19}$, in implementation order, is

$$
y = [\,\underbrace{O_{PD1},\, O_{CTLA4}}_{\text{Module 1}} \mid
\underbrace{T_{naive},\, T_{eff},\, T_{reg}}_{\text{Module 2}} \mid
\underbrace{IFN,\, TNF,\, IL2,\, IL17}_{\text{Module 3}} \mid
\underbrace{Thyro,\, Colloid,\, TPO,\, D,\, M,\, TPOAb,\, TgAb}_{\text{Module 4}} \mid
\underbrace{T_4,\, T_3,\, TSH}_{\text{Module 5}}\,]
$$

where $D$ is `cumulative_damage` and $M$ is `immune_memory`.

| Symbol | State | Meaning | Unit / scale |
|---|---|---|---|
| $O_{PD1}$ | O_pd1 | PD-1 axis receptor occupancy | 0-1 |
| $O_{CTLA4}$ | O_ctla4 | CTLA-4 axis receptor occupancy | 0-1 |
| $T_{naive}$ | T_naive | Naive T cells | cells (scaled) |
| $T_{eff}$ | T_eff | Effector T cells | cells (scaled) |
| $T_{reg}$ | T_reg | Regulatory T cells | cells (scaled) |
| $IFN$ | IFN | Interferon-gamma | pg/mL |
| $TNF$ | TNF | Tumor necrosis factor-alpha | pg/mL |
| $IL2$ | IL2 | Interleukin-2 | pg/mL |
| $IL17$ | IL17 | Interleukin-17 | pg/mL |
| $Thyro$ | Thyro | Functional thyroid mass | 0-1 (fraction of $Thyro_{max}$) |
| $Colloid$ | Colloid | Stored preformed-hormone pool | relative |
| $TPO$ | TPO | Thyroid peroxidase activity | 0-1 |
| $D$ | cumulative_damage | Latent tissue-damage integrator | relative |
| $M$ | immune_memory | Immune-memory amplifier | relative |
| $TPOAb$ | TPOAb | Thyroid peroxidase antibody titer | titer units |
| $TgAb$ | TgAb | Thyroglobulin antibody titer | titer units |
| $T_4$ | T4 | Thyroxine | ug/dL scale |
| $T_3$ | T3 | Triiodothyronine | ug/dL scale |
| $TSH$ | TSH | Thyroid-stimulating hormone | mIU/L |

## 3. Pharmacokinetics

Each drug follows an analytic one-compartment multi-dose profile with linear
clearance. With body weight $BW = 70$ kg, dose interval $\tau$, clearance $CL$,
volume $V$, and per-dose amount $\text{dose}_{mg} = \text{dose}_{mg/kg}\cdot BW$,
the concentration (ng/mL) from superposition of all doses given at $t_k = k\tau
\le t$ is

$$
C_{\text{drug}}(t) = \sum_{k:\, t_k \le t}
\frac{\text{dose}_{mg}\cdot 10^{6}}{V\cdot 10^{3}}\,
\exp\!\left(-\frac{CL\,(t - t_k)}{V}\right).
$$

Per-drug PK parameters ($CL$, $V$, dose, $\tau$, $EC50_{occ}$, potency, target
axis) are listed in Table P.

## 4. Receptor Occupancy Equilibrium

For each axis $a \in \{PD1, CTLA4\}$, the concentration-dependent equilibrium
occupancy aggregates the contributions of all active drugs targeting that axis
(anti-PD-1 and anti-PD-L1 both act on the PD-1 axis; ipilimumab on the CTLA-4
axis), capped at 1:

$$
occ^{\text{eq}}_a(t) = \min\!\left(1,\ \sum_{\text{drug} \in a}
\frac{C_{\text{drug}}(t)}{C_{\text{drug}}(t) + EC50_{occ,\text{drug}}}\cdot
\text{potency}_{\text{drug}}\right).
$$

## 5. Module 1 - Checkpoint Pharmacology

Occupancy states relax toward their equilibria at rate $k_{occ}$:

$$
\frac{dO_{PD1}}{dt} = k_{occ}\,\big(occ^{\text{eq}}_{PD1} - O_{PD1}\big),
\qquad
\frac{dO_{CTLA4}}{dt} = k_{occ}\,\big(occ^{\text{eq}}_{CTLA4} - O_{CTLA4}\big).
$$

## 6. Module 2 - T-Cell Dynamics

Treg suppression of effectors is weakened by CTLA-4 blockade (the mechanistic
basis of combination synergy):

$$
\sigma = treg_{supp}\,(1 - treg_{syn}\,O_{CTLA4}), \qquad
\text{supp} = \frac{1}{1 + \sigma\,(T_{reg}/T_{reg0})},
$$

$$
\text{act} = \big(w_{pd1}\,O_{PD1} + w_{ctla4}\,O_{CTLA4}\big)\,\text{supp},
\qquad S_{eff0} = \beta_{eff}\,T_{eff0},
$$

$$
\text{prime} = k_{prime}\,(1 + w_{ctla4,prime}\,O_{CTLA4}).
$$

$$
\frac{dT_{naive}}{dt} = s_{naive} - \text{prime}\,T_{naive} - d_{naive}\,T_{naive},
$$

$$
\frac{dT_{eff}}{dt} = S_{eff0}\,(1 + \text{act})
+ \delta_{il2}\,IL2\,T_{eff}\,\text{supp} - \beta_{eff}\,T_{eff},
$$

$$
\frac{dT_{reg}}{dt} = k_{treg,src} - d_{treg}\,T_{reg}
- k_{ctla4,treg}\,O_{CTLA4}\,T_{reg}.
$$

## 7. Module 3 - Cytokine Network

With normalized effector drive $\hat{e} = T_{eff}/T_{eff0}$:

$$
\frac{dIFN}{dt} = \varepsilon_{ifn}\,\hat{e}\,
\left(1 + \frac{IFN}{IFN + 80}\right)
\left(1 + \kappa_{tnf}\frac{TNF}{TNF + 50}\right) - k_{ifn}\,IFN,
$$

$$
\frac{dTNF}{dt} = \varepsilon_{tnf}\,\hat{e} - k_{tnf}\,TNF, \qquad
\frac{dIL2}{dt} = \varepsilon_{il2}\,\hat{e} - k_{il2}\,IL2,
$$

$$
\frac{dIL17}{dt} = \frac{\varepsilon_{il17}\,\hat{e}}{1 + T_{reg}/T_{reg0}}
- k_{il17}\,IL17.
$$

## 8. Module 4 - Thyroid Gland and Signaling

**Cumulative damage and immune memory.** With cytokine drive
$c = IFN + 0.5\,TNF$, time gate
$g(t) = \mathrm{clip}\!\big((t - t_{min})/\tau_{ramp},\,0,\,1\big)$, and memory
amplifier $m = 1 + (\mu_{f} - 1)\,M$:

$$
\text{accum} =
\begin{cases}
\lambda_{D}\,\dfrac{c}{c + \kappa_{D}}\,g(t)\,m\,\phi, & c \ge c_{thr}\ \text{and}\ g(t) > 0,\\[2mm]
0, & \text{otherwise,}
\end{cases}
$$

$$
\frac{dD}{dt} = \text{accum} - k_{rep}\,D, \qquad
\frac{dM}{dt} =
\begin{cases}
\rho_{M}\,(c/150), & c \ge c_{thr}\ \text{and}\ g(t)>0,\\
-5\times10^{-4}\,M, & \text{otherwise,}
\end{cases}
$$

where $\phi$ is the patient susceptibility multiplier (Section 11). The
always-active repair term $k_{rep}D$ creates a sub-threshold equilibrium, so
low-drive/low-susceptibility patients plateau below the disease threshold and
never develop dysfunction (decoupling incidence from onset).

**Graded disease activation.** With a slowly growing threshold
$D_{thr}(t) = D_0 + r_{thr}\,t$:

$$
a(t) = \mathrm{clip}\!\left(\frac{D - D_{thr}(t)}{w_{act}},\ 0,\ 1\right),
\qquad
\Phi_{IFN} = \frac{IFN^{h}}{EC50_{IFN}^{h} + IFN^{h}}\ (h = Hill_{IFN}).
$$

**Thyrocyte mass, TPO, colloid.**

$$
\text{death} = a(t)\,k_{death}\,\Phi_{IFN}\,Thyro\,\phi\,m, \qquad
\frac{dThyro}{dt} = -\text{death} + k_{regen}\,(Thyro_{max} - Thyro),
$$

$$
\frac{dTPO}{dt} = k_{tpo,rec}\,(1 - TPO)
- a(t)\,k_{tpo,sup}\!\left(\Phi_{IFN} + \frac{TNF}{TNF + 100}\right) TPO,
$$

$$
\text{burst} = k_{cb}\,\text{death}\,Colloid, \qquad
\frac{dColloid}{dt} = k_{cs}\,Thyro\,TPO - k_{cr}\,Colloid - \text{burst}.
$$

The destructive colloid burst is what produces the transient thyrotoxic (hormone
release) spike before synthetic failure drives hypothyroidism.

**Autoantibodies.** Production scales with effector expansion above baseline
times baseline propensity and susceptibility:

$$
u = \frac{\max(0,\, T_{eff} - T_{eff0})}{e_{ref}}
\big(1 + \eta_{HLA}\,TPOAb_0\big)\,\phi,
$$

$$
\frac{dTPOAb}{dt} = k_{tpoab}^{+}\,u - k_{tpoab}^{-}\,TPOAb, \qquad
\frac{dTgAb}{dt} = k_{tgab}^{+}\,u - k_{tgab}^{-}\,TgAb.
$$

## 9. Module 5 - HPT Axis

TSH is trophic (elevated TSH up-regulates the surviving gland's output),
resting at unity at baseline:

$$
\text{tsh}_{ex} = \max(0,\, TSH - TSH_{set}), \quad
\text{tr} = 1 + k_{tr}\frac{\text{tsh}_{ex}}{\text{tsh}_{ex} + h_{tr}}, \quad
\text{synth} = Thyro\cdot TPO\cdot \text{tr}.
$$

$$
\frac{dT_4}{dt} = k_{syn,T4}\,\text{synth} + f_{T4}\,\text{burst}
- k_{deg,T4}\,T_4 - k_{conv}\,T_4,
$$

$$
\frac{dT_3}{dt} = k_{syn,T3}\,\text{synth} + k_{conv}\,T_4 + f_{T3}\,\text{burst}
- k_{deg,T3}\,T_3.
$$

TSH follows bounded negative feedback that stays non-negative, rises when hormone
falls, is suppressed during the thyrotoxic spike, and saturates smoothly toward a
ceiling:

$$
r = TSH_{set}\left(\frac{T4_{set}}{\max(T_4,1)}\right)^{h_{fb}}, \quad
TSH^{\ast} = \frac{r}{\sqrt{1 + (r/TSH_{ceil})^{2}}}, \quad
\frac{dTSH}{dt} = k_{TSH}\,(TSH^{\ast} - TSH).
$$

## 10. Initial Conditions (pre-treatment baseline)

$$
O_{PD1}=O_{CTLA4}=0,\quad T_{naive}=T_{naive0},\quad T_{eff}=T_{eff0},\quad
T_{reg}=T_{reg0},
$$
$$
IFN=TNF=0,\quad IL2=0.08,\quad IL17=0,\quad Thyro=Thyro_{max},\quad Colloid=1.0,
$$
$$
TPO=1,\quad D=0,\quad M=0,\quad TPOAb=TPOAb_0,\quad TgAb=0,\quad
T_4=T4_{set},\ T_3=T3_{set},\ TSH=TSH_{set}.
$$

## 11. Patient Susceptibility Mixture

Overall autoimmune susceptibility $\phi$ is drawn from a two-component lognormal
mixture (a minority high-risk subpopulation vs. a low-risk majority). For each
patient, with high-risk fraction $\pi = 0.092$:

$$
z \sim \text{Bernoulli}(\pi),\quad
\text{med} = \begin{cases}1.70 & z=1\\ 0.45 & z=0\end{cases},\quad
\phi = \mathrm{clip}\big(\text{Lognormal}(\ln \text{med},\,\sigma=0.30),\ 0.20,\ 2.8\big).
$$

Per-patient covariates (age, sex, HLA-DQ risk, baseline TSH, baseline TPOAb) map
onto $\phi$ and the antibody drive in the population and cohort samplers.

## 12. Thyroid-Status Classification

Each time point is classified from $(TSH, T_4, T_3)$ (thresholds from
`classification.py`):

| Condition | Status | Grade |
|---|---|---|
| $T_4 \ge 22$ or $T_3 \ge 8.5$ | hyperthyroid | thyrotoxic (hyper grade 3) |
| $T_4 \ge 16$ or $T_3 \ge 6.5$ | hyperthyroid | overt (hyper grade 2) |
| $TSH > 50$ or $T_3 < 2.0$ | hypothyroid | grade 4 |
| $TSH > 20$ or $T_3 < 2.5$ | hypothyroid | grade 3 |
| $TSH > 10$ or $T_3 < 3.1$ | hypothyroid | grade 2 |
| $TSH > 4.5$ | hypothyroid | grade 1 |
| otherwise | euthyroid | 0 |

A patient is counted as having hypothyroidism / hyperthyroidism if the
corresponding status occurs at any time point over the horizon; a case is
**biphasic** if a hyperthyroid phase precedes a hypothyroid phase.

## 13. Numerical Integration

The system is integrated with SciPy `solve_ivp` using the LSODA stiff/non-stiff
switching solver with relative tolerance $10^{-6}$, absolute tolerance
$10^{-9}$, and `max_step = 1.0` day. On rare non-convergence, the solver
automatically retries with looser tolerances ($10^{-4}$, $10^{-7}$, `max_step`
0.5). The reference horizon is 180 days for incidence/onset endpoints and 365
days for cohort follow-up.

## Table P - Per-Drug Pharmacokinetics and Occupancy

| Drug | Class | $CL$ | $V$ | Dose (mg/kg) | $\tau$ (d) | $EC50_{occ}$ (ng/mL) | Potency | Axis |
|---|---|---|---|---|---|---|---|---|
| nivolumab | PD-1 | 0.20 | 6.0 | 3 | 14 | 6600 | 1.00 | PD-1 |
| pembrolizumab | PD-1 | 0.22 | 6.0 | 2 | 21 | 5800 | 0.95 | PD-1 |
| atezolizumab | PD-L1 | 0.25 | 6.5 | 15 | 21 | 45000 | 0.55 | PD-1 |
| durvalumab | PD-L1 | 0.24 | 6.2 | 10 | 14 | 35000 | 0.62 | PD-1 |
| ipilimumab | CTLA-4 | 0.15 | 7.0 | 3 | 21 | 20000 | 0.85 | CTLA-4 |

The combination regimen (nivolumab + ipilimumab) drives both axes simultaneously.

## Table Q - Physiological Parameters (calibrated / literature-anchored)

| Symbol | Code name | Value | Role |
|---|---|---|---|
| $k_{occ}$ | k_occ | 0.5 | occupancy relaxation rate |
| $s_{naive}$ | s_naive | 5.0 | naive source |
| $d_{naive}$ | d_naive | 0.02 | naive death |
| $k_{prime}$ | k_prime | 0.010 | naive-to-effector priming drain |
| $w_{ctla4,prime}$ | w_ctla4_prime | 6.0 | CTLA-4 enhancement of priming |
| $w_{pd1}$ | w_pd1_eff | 15.0 | PD-1 effector activation weight |
| $w_{ctla4}$ | w_ctla4_eff | 5.5 | CTLA-4 effector activation weight |
| $treg_{syn}$ | treg_synergy | 0.95 | CTLA-4 weakening of Treg suppression |
| $\beta_{eff}$ | beta_eff | 0.12 | effector death |
| $\delta_{il2}$ | delta_il2 | 0.004 | IL-2-driven proliferation |
| $k_{treg,src}$ | k_treg_src | 15.0 | Treg source |
| $d_{treg}$ | d_treg | 0.05 | Treg turnover |
| $k_{ctla4,treg}$ | k_ctla4_treg | 0.08 | CTLA-4 depletion of Treg |
| $treg_{supp}$ | treg_supp | 1.0 | baseline Treg suppression |
| $T_{eff0}$ | T_eff0 | 1500 | baseline effector scale |
| $T_{reg0}$ | T_reg0 | 300 | baseline Treg scale |
| $T_{naive0}$ | T_naive0 | 167 | baseline naive scale |
| $\varepsilon_{ifn}$ | eps_ifn | 20.0 | IFN production |
| $k_{ifn}$ | k_clear_ifn | 1.2 | IFN clearance |
| $\varepsilon_{tnf}$ | eps_tnf | 1.2 | TNF production |
| $k_{tnf}$ | k_clear_tnf | 1.5 | TNF clearance |
| $\varepsilon_{il2}$ | eps_il2 | 1.0 | IL-2 production |
| $k_{il2}$ | k_clear_il2 | 2.0 | IL-2 clearance |
| $\varepsilon_{il17}$ | eps_il17 | 0.8 | IL-17 production |
| $k_{il17}$ | k_clear_il17 | 1.4 | IL-17 clearance |
| $\kappa_{tnf}$ | ifn_tnf_crosstalk | 0.3 | TNF potentiation of IFN |
| $EC50_{IFN}$ | EC50_IFN_death | 85.0 | IFN EC50 for thyrocyte death |
| $Hill_{IFN}$ | Hill_IFN | 1.2 | Hill coefficient |
| $c_{thr}$ | cytokine_threshold_pg_ml | 60.0 | damage-accumulation gate |
| $D_0$ | base_damage_threshold | 0.020 | base disease threshold |
| $r_{thr}$ | damage_threshold_growth_rate | 5e-5 | threshold growth rate |
| $\kappa_{D}$ | damage_half_sat | 150.0 | damage half-saturation |
| $\lambda_{D}$ | damage_rate | 7.0e-4 | damage accumulation rate |
| $k_{rep}$ | k_damage_repair | 0.010 | damage repair/turnover |
| $w_{act}$ | disease_activation_width | 0.028 | graded activation band width |
| $t_{min}$ | minimum_exposure_days | 25.0 | minimum exposure before damage |
| $\tau_{ramp}$ | damage_ramp_time | 12.0 | damage time-gate ramp |
| $k_{death}$ | k_death | 0.06 | cytotoxic thyrocyte death scale |
| $k_{regen}$ | k_regen | 0.020 | follicular regeneration |
| $\rho_M$ | memory_accumulation_rate | 0.0005 | immune-memory accumulation |
| $\mu_f$ | immune_memory_factor | 1.1 | memory amplification factor |
| $k_{tpo,rec}$ | k_tpo_rec | 0.05 | TPO recovery |
| $k_{tpo,sup}$ | k_tpo_sup | 0.35 | TPO suppression |
| $k_{cs}$ | k_coll_syn | 0.8 | colloid synthesis |
| $k_{cr}$ | k_coll_rel | 0.02 | baseline colloid release |
| $k_{cb}$ | k_coll_burst | 5.4 | destructive colloid burst |
| $k_{tpoab}^{+}$ | k_tpoab_prod | 0.06 | TPOAb production |
| $k_{tpoab}^{-}$ | k_tpoab_decay | 0.01 | TPOAb decay |
| $k_{tgab}^{+}$ | k_tgab_prod | 0.04 | TgAb production |
| $k_{tgab}^{-}$ | k_tgab_decay | 0.012 | TgAb decay |
| $e_{ref}$ | ab_effector_ref | 3000 | effector reference for antibodies |
| $k_{syn,T4}$ | k_syn_T4 | 1.788 | T4 synthesis |
| $k_{syn,T3}$ | k_syn_T3 | 2.726 | T3 synthesis |
| $k_{deg,T4}$ | k_deg_T4 | 0.099 | T4 degradation |
| $k_{deg,T3}$ | k_deg_T3 | 0.693 | T3 degradation |
| $k_{conv}$ | k_conv_T4_T3 | 0.05 | peripheral T4-to-T3 conversion |
| $f_{T4}$ | release_T4_frac | 0.8 | colloid burst appearing as T4 |
| $f_{T3}$ | release_T3_frac | 0.2 | colloid burst appearing as T3 |
| $T4_{set}$ | T4_set | 12.0 | euthyroid T4 setpoint |
| $T3_{set}$ | T3_set | 4.8 | euthyroid T3 setpoint |
| $TSH_{set}$ | TSH_set | 1.5 | euthyroid TSH setpoint |
| $h_{fb}$ | TSH_feedback_hill | 2.5 | TSH feedback Hill exponent |
| $k_{TSH}$ | k_metab_TSH | 0.15 | TSH relaxation rate |
| $TSH_{ceil}$ | TSH_ceiling | 200.0 | TSH saturation ceiling |
| $k_{tr}$ | k_tsh_trophic | 8.0 | max trophic synthesis fold-increase |
| $h_{tr}$ | tsh_trophic_half | 12.0 | TSH excess at half-maximal trophic drive |

Calibrated parameters (susceptibility mixture, onset/damage, per-drug potency,
CTLA-4 effector weight, Treg synergy) are those that place 180-day per-drug
hypothyroidism incidence within published ranges; see
`scripts/calibration/calibrate_expanded_model.py` and
`results/v1/calibration_report.json`.
