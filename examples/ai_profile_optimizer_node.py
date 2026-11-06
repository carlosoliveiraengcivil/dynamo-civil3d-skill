# -*- coding: utf-8 -*-
"""
EXEMPLO AVANÇADO: Otimizador Evolucionário de Greide Viário & Compensação de Terraplenagem (IA + DNIT)
Motor CPython3 para Dynamo no Autodesk Civil 3D.

Entradas do Nó (IN):
  IN[0] (bool)   : Executar Otimização e Gerar Perfil no Civil 3D
  IN[1] (str)    : Nome do Alinhamento Horizontal (vazio = 1º alinhamento do DWG)
  IN[2] (str)    : Nome da Superfície de Terreno Natural (vazio = 1ª TinSurface do DWG)
  IN[3] (float)  : Rampa Máxima Permitida em % (ex: 6.0 para Classe I DNIT)
  IN[4] (float)  : Espaçamento entre PVIs em metros (ex: 160.0)
  IN[5] (float)  : Fator de Empolamento / Homogeneização Corte-Aterro (ex: 1.25)
  IN[6] (str)    : Nome do Perfil Otimizado a Criar (ex: "GREIDE_IA_OTIMIZADO")
"""

import sys
import math
import random
import traceback
import clr

clr.AddReference("acmgd")
clr.AddReference("acdbmgd")
clr.AddReference("accoremgd")
clr.AddReference("AecBaseMgd")
clr.AddReference("AeccDbMgd")

from Autodesk.AutoCAD.ApplicationServices import *
from Autodesk.AutoCAD.DatabaseServices import *
import Autodesk.AutoCAD.Geometry as AcGeom
from Autodesk.Civil.ApplicationServices import *
from Autodesk.Civil.DatabaseServices import *


class EvolutionaryGreideEngine:
    """
    Motor de Inteligência Artificial (Algoritmo Genético de Codificação Real)
    para síntese de greide ótimo com balanço de massas (Bruckner) e conformidade DNIT.
    """

    def __init__(
        self,
        pvi_stations,
        pvi_tn_elevs,
        sample_stations,
        sample_tn_elevs,
        max_grade_pct=6.0,
        min_grade_pct=0.35,
        swell_factor=1.25,
        platform_width=12.0,
        pop_size=64,
        generations=90,
    ):
        self.pvi_sta = list(pvi_stations)
        self.pvi_tn = list(pvi_tn_elevs)
        self.sample_sta = list(sample_stations)
        self.sample_tn = list(sample_tn_elevs)
        self.max_grade = max_grade_pct / 100.0
        self.min_grade = min_grade_pct / 100.0
        self.swell = swell_factor
        self.width = platform_width
        self.pop_size = pop_size
        self.generations = generations
        random.seed(2026)

    def _elev_at(self, pvi_z, sta):
        if sta <= self.pvi_sta[0]:
            return pvi_z[0]
        if sta >= self.pvi_sta[-1]:
            return pvi_z[-1]
        for i in range(len(self.pvi_sta) - 1):
            s0, s1 = self.pvi_sta[i], self.pvi_sta[i + 1]
            if s0 <= sta <= s1:
                t = (sta - s0) / max(1e-6, s1 - s0)
                return pvi_z[i] + t * (pvi_z[i + 1] - pvi_z[i])
        return pvi_z[-1]

    def evaluate_candidate(self, pvi_z):
        penalty = 0.0
        max_obs_grade = 0.0

        # 1. Restrições normativas de rampa máxima e mínima
        for i in range(len(self.pvi_sta) - 1):
            ds = max(1e-6, self.pvi_sta[i + 1] - self.pvi_sta[i])
            g = abs(pvi_z[i + 1] - pvi_z[i]) / ds
            if g > max_obs_grade:
                max_obs_grade = g
            if g > self.max_grade:
                penalty += 2.0e6 * ((g - self.max_grade) ** 2)
            if g < self.min_grade:
                penalty += 4.0e4 * ((self.min_grade - g) ** 2)

        # 2. Integração prismoidal simplificada de Corte e Aterro
        cut_vol = 0.0
        fill_vol = 0.0
        for k, s in enumerate(self.sample_sta):
            z_tn = self.sample_tn[k]
            z_pr = self._elev_at(pvi_z, s)
            dh = z_pr - z_tn
            step = (self.sample_sta[k] - self.sample_sta[k - 1]) if k > 0 else 20.0
            if dh < 0.0:
                h_c = abs(dh)
                area_c = (self.width + 1.0 * h_c) * h_c
                cut_vol += area_c * step
            else:
                h_f = dh
                area_f = (self.width + 1.5 * h_f) * h_f
                fill_vol += area_f * step

        imbalance = abs(cut_vol * self.swell - fill_vol)
        total_earthwork = cut_vol + fill_vol
        fitness_cost = 2.5 * imbalance + 0.45 * total_earthwork + penalty
        return fitness_cost, cut_vol, fill_vol, imbalance, max_obs_grade * 100.0

    def solve(self):
        n = len(self.pvi_sta)
        if n <= 2:
            metrics = self.evaluate_candidate(self.pvi_tn)
            return list(self.pvi_tn), metrics

        pop = []
        for _ in range(self.pop_size):
            cand = list(self.pvi_tn)
            for j in range(1, n - 1):
                cand[j] += random.uniform(-3.0, 3.0)
            pop.append(cand)

        best_z = list(self.pvi_tn)
        best_m = self.evaluate_candidate(best_z)

        for gen in range(self.generations):
            ranked = []
            for ind in pop:
                m = self.evaluate_candidate(ind)
                ranked.append((m[0], ind, m))
            ranked.sort(key=lambda item: item[0])

            if ranked[0][0] < best_m[0]:
                best_z = list(ranked[0][1])
                best_m = ranked[0][2]

            elite_n = max(4, self.pop_size // 5)
            next_pop = [list(x[1]) for x in ranked[:elite_n]]

            while len(next_pop) < self.pop_size:
                p1 = random.choice(ranked[: elite_n * 2])[1]
                p2 = random.choice(ranked[: elite_n * 2])[1]
                child = list(p1)
                for j in range(1, n - 1):
                    alpha = random.uniform(-0.15, 1.15)
                    child[j] = p1[j] + alpha * (p2[j] - p1[j])
                    if random.random() < 0.25:
                        sigma = 1.0 * (1.0 - gen / self.generations) + 0.04
                        child[j] += random.gauss(0.0, sigma)
                next_pop.append(child)
            pop = next_pop

        return best_z, best_m


def run_optimizer():
    run_flag = bool(IN[0]) if len(IN) > 0 and IN[0] is not None else True
    alg_name_in = str(IN[1]).strip() if len(IN) > 1 and IN[1] is not None else ""
    surf_name_in = str(IN[2]).strip() if len(IN) > 2 and IN[2] is not None else ""
    max_grade_pct = float(IN[3]) if len(IN) > 3 and IN[3] is not None else 6.0
    pvi_spacing = float(IN[4]) if len(IN) > 4 and IN[4] is not None else 160.0
    swell_factor = float(IN[5]) if len(IN) > 5 and IN[5] is not None else 1.25
    out_profile_name = str(IN[6]).strip() if len(IN) > 6 and IN[6] is not None else "GREIDE_IA_OTIMIZADO"

    if not run_flag:
        return {"status": "AGUARDANDO", "mensagem": "Ative o parâmetro 'Executar' no Dynamo Player."}

    adoc = Application.DocumentManager.MdiActiveDocument
    db = adoc.Database
    civdoc = CivilApplication.ActiveDocument

    with adoc.LockDocument():
        with db.TransactionManager.StartTransaction() as tr:
            # 1. Localizar Alinhamento
            target_alg = None
            for aid in civdoc.GetAlignmentIds():
                a = tr.GetObject(aid, OpenMode.ForRead)
                if isinstance(a, Alignment):
                    if target_alg is None or (alg_name_in and a.Name.lower() == alg_name_in.lower()):
                        target_alg = a
                        if alg_name_in and a.Name.lower() == alg_name_in.lower():
                            break

            # 2. Localizar Superfície TIN
            target_surf = None
            for sid in civdoc.GetSurfaceIds():
                s = tr.GetObject(sid, OpenMode.ForRead)
                if isinstance(s, TinSurface):
                    if target_surf is None or (surf_name_in and s.Name.lower() == surf_name_in.lower()):
                        target_surf = s
                        if surf_name_in and s.Name.lower() == surf_name_in.lower():
                            break

            if target_alg is None or target_surf is None:
                return {
                    "status": "ERRO",
                    "mensagem": "Certifique-se de que o DWG contém ao menos 1 Alinhamento e 1 Superfície TIN.",
                }

            sta_0 = float(target_alg.StartingStation)
            sta_f = float(target_alg.EndingStation)

            def get_tn_at_station(st):
                x_ref = clr.Reference[float](0.0)
                y_ref = clr.Reference[float](0.0)
                target_alg.PointLocation(st, 0.0, x_ref, y_ref)
                return float(target_surf.FindElevationAtXY(float(x_ref.Value), float(y_ref.Value)))

            # Amostragem densa (a cada 20m) e geração das estacas dos PVIs
            sample_sta = []
            sample_tn = []
            curr_s = sta_0
            while curr_s < sta_f:
                try:
                    sample_tn.append(get_tn_at_station(curr_s))
                    sample_sta.append(curr_s)
                except Exception:
                    pass
                curr_s += 20.0
            try:
                sample_tn.append(get_tn_at_station(sta_f))
                sample_sta.append(sta_f)
            except Exception:
                pass

            pvi_sta = []
            pvi_tn = []
            curr_pvi = sta_0
            while curr_pvi < sta_f - (pvi_spacing * 0.4):
                try:
                    pvi_tn.append(get_tn_at_station(curr_pvi))
                    pvi_sta.append(curr_pvi)
                except Exception:
                    pass
                curr_pvi += max(40.0, pvi_spacing)
            pvi_sta.append(sta_f)
            pvi_tn.append(sample_tn[-1])

            # 3. Executar Motor de Inteligência Artificial (Algoritmo Genético)
            engine = EvolutionaryGreideEngine(
                pvi_sta,
                pvi_tn,
                sample_sta,
                sample_tn,
                max_grade_pct=max_grade_pct,
                swell_factor=swell_factor,
            )
            opt_z, metrics = engine.solve()

            # 4. Criar Perfil de Projeto Otimizado no Civil 3D
            layer_id = target_alg.LayerId
            prof_style_id = civdoc.Styles.ProfileStyles[0]
            label_set_id = civdoc.Styles.LabelSetStyles.ProfileLabelSetStyles[0]

            prof_id = Profile.CreateByLayout(
                out_profile_name, target_alg.ObjectId, layer_id, prof_style_id, label_set_id
            )
            prof = tr.GetObject(prof_id, OpenMode.ForWrite)

            for st_val, z_val in zip(pvi_sta, opt_z):
                prof.PVIs.AddPVI(float(st_val), float(z_val))

            # Adicionar curvas parabólicas nos PVIs internos
            curve_len = min(80.0, pvi_spacing * 0.45)
            for idx in range(1, len(pvi_sta) - 1):
                try:
                    prof.Entities.AddFreeSymmetricParabolaByLength(
                        float(pvi_sta[idx]), float(opt_z[idx]), float(curve_len)
                    )
                except Exception:
                    pass

            tr.Commit()

            return {
                "status": "SUCESSO",
                "alinhamento": target_alg.Name,
                "superficie_terreno": target_surf.Name,
                "perfil_gerado": out_profile_name,
                "quantidade_pvis": len(pvi_sta),
                "volume_corte_estimado_m3": round(metrics[1], 2),
                "volume_aterro_estimado_m3": round(metrics[2], 2),
                "desequilibrio_compensacao_m3": round(metrics[3], 2),
                "rampa_maxima_observada_pct": round(metrics[4], 2),
                "limite_normativo_dnit_pct": max_grade_pct,
                "pvis_otimizados": [
                    {"estaca_m": round(s, 2), "cota_tn_m": round(tn, 3), "cota_ia_m": round(zi, 3)}
                    for s, tn, zi in zip(pvi_sta, pvi_tn, opt_z)
                ],
            }


OUT = run_optimizer()
