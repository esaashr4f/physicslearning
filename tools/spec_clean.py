import json, re, sys
src, out = sys.argv[1], sys.argv[2]
d = json.load(open(src))
FIX = {
 "2.3.1(d)": "resolving a vector into two perpendicular components; Fx = F cos θ; Fy = F sin θ",
 "3.1.2(a)(i)": "the equations of motion for constant acceleration in a straight line, including motion of bodies falling in a uniform gravitational field without air resistance: v = u + at; s = ½(u + v)t; s = ut + ½at²; v² = u² + 2as",
 "3.2.4(a)": "density; ρ = m/V",
 "3.2.4(b)": "pressure; p = F/A for solids, liquids and gases",
 "3.2.4(c)": "p = hρg; upthrust on an object in a fluid; Archimedes’ principle",
 "3.3.1(b)": "W = Fx cos θ for work done by a force",
 "3.3.2(a)": "kinetic energy of an object; Ek = ½mv²",
 "3.3.2(b)": "gravitational potential energy of an object in a uniform gravitational field; Ep = mgh",
 "3.3.3(a)": "power; the unit watt; P = W/t",
 "3.3.3(c)": "efficiency of a mechanical system; efficiency = useful output energy / total input energy × 100%",
 "3.4.2(a)": "force–extension (or compression) graph; work done is area under graph",
 "3.4.2(b)": "elastic potential energy; E = ½Fx; E = ½kx²",
 "3.4.2(c)": "stress, strain and ultimate tensile strength",
 "4.4.2(c)": "plane polarised waves; polarisation of electromagnetic waves",
 "4.4.3(a)(i)": "the principle of superposition of waves",
 "4.5.3(b)": "diffraction of electrons travelling through a thin slice of polycrystalline graphite by the atoms of graphite and the spacing between the atoms",
 "4.4.3(f)": "Young double-slit experiment using visible light",
 "4.5.1(b)": "photon as a quantum of energy of electromagnetic radiation",
 "4.5.1(d)": "the electronvolt (eV) as a unit of energy",
 "3.4.2(d)(i)": "Young modulus = tensile stress / tensile strain; E = σ/ε",
 "3.5.1(c)": "net force = rate of change of momentum; F = Δp/Δt",
 "4.1.1(a)": "electric current as rate of flow of charge; I = ΔQ/Δt",
 "4.2.2(e)": "energy transfer eV = ½mv² for electrons and other charged particles",
 "4.2.3(a)": "resistance; R = V/I; the unit ohm",
 "4.2.4(a)(i)": "resistivity of a material; the equation R = ρL/A",
 "4.2.5(a)": "the equations P = VI, P = I²R and P = V²/R",
 "4.3.1(c)": "total resistance of two or more resistors in series; R = R1 + R2 + …",
 "4.3.1(d)": "total resistance of two or more resistors in parallel; 1/R = 1/R1 + 1/R2 + …",
 "4.3.2(b)": "terminal p.d.; ‘lost volts’",
 "4.3.2(c)(i)": "the equations E = I(R + r) and E = V + Ir",
 "4.3.3(c)(i)": "potential divider equations e.g. Vout = R2/(R1 + R2) × Vin and V1/V2 = R1/R2",
 "4.4.1(c)": "the equation f = 1/T",
 "4.4.1(d)": "the wave equation v = fλ",
 "4.4.1(g)": "intensity of a progressive wave; I = P/A; intensity ∝ (amplitude)²",
 "4.4.2(d)": "refraction of light; refractive index; n = c/v; n sin θ = constant at a boundary where θ is the angle to the normal",
 "4.4.2(e)": "critical angle; sin C = 1/n; total internal reflection for light",
 "4.4.3(g)(i)": "λ = ax/D for all waves where a ≪ D",
 "4.4.4(f)": "the idea that the separation between adjacent nodes (or antinodes) is equal to λ/2, where λ is the wavelength of the progressive wave",
 "4.5.1(c)": "energy of a photon; E = hf and E = hc/λ",
 "4.5.1(e)(i)": "using LEDs and the equation eV = hc/λ to estimate the value of Planck constant h",
 "4.5.2(c)": "Einstein’s photoelectric equation hf = φ + KEmax",
 "4.5.3(c)": "the de Broglie equation λ = h/p",
}
clean = []
for o in d["outcomes"]:
    t = re.split(r"\s+(?:Module \d:|Prior knowledge|5c\. )", o["text"])[0]
    t = re.sub(r"\b([a-zA-Z])\s*[\x00-\x1f\x7f]+\s*([a-z])", r"\1\2", t)
    t = re.sub(r"[\x00-\x1f\x7f]", "", t)
    t = re.sub(r"\b([a-zA-Z])[\s\u00a0\u2009\u200a\u2002\u2003]{2,}([a-z])", r"\1\2", t).strip()
    if o["code"] in FIX and FIX[o["code"]]:
        t = FIX[o["code"]]
    clean.append({"code": o["code"], "section": o["section"], "text": t})
# parent stems like 1.1.3(d) whose roman children exist keep their stem text
d["outcomes"] = clean
json.dump(d, open(out, "w"), indent=1, ensure_ascii=False)
print(len(clean))
for o in clean:
    if o["section"] in ("3.4.2", "4.4.3", "4.5.1"):
        print(o["code"], "|", o["text"][:140])
