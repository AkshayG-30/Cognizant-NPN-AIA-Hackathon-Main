from xml.etree.ElementTree import Element, SubElement, ElementTree
from xml.sax.saxutils import escape

OUTPUT_FILE = "CarePath_System_Architecture.drawio"

# ------------------------------------------------------------
# CarePath - System Architecture
# Native draw.io XML generator
# ------------------------------------------------------------

mxfile = Element("mxfile", {
    "host": "app.diagrams.net",
    "modified": "2026-08-23T00:00:00.000Z",
    "agent": "Python draw.io generator",
    "version": "29.0.0",
    "type": "device"
})

diagram = SubElement(mxfile, "diagram", {"id": "carepath-architecture", "name": "CarePath Architecture"})

model = SubElement(diagram, "mxGraphModel", {
    "dx": "1600",
    "dy": "1000",
    "grid": "1",
    "gridSize": "10",
    "guides": "1",
    "tooltips": "1",
    "connect": "1",
    "arrows": "1",
    "fold": "1",
    "page": "1",
    "pageScale": "1",
    "pageWidth": "1600",
    "pageHeight": "1000",
    "math": "0",
    "shadow": "0"
})

root = SubElement(model, "root")
SubElement(root, "mxCell", {"id": "0"})
SubElement(root, "mxCell", {"id": "1", "parent": "0"})

counter = 2

def new_id(prefix="node"):
    global counter
    value = f"{prefix}_{counter}"
    counter += 1
    return value

def add_text(text, x, y, w, h, style="", parent="1"):
    cell_id = new_id("text")
    SubElement(root, "mxCell", {
        "id": cell_id,
        "value": escape(text),
        "style": (
            "text;html=1;whiteSpace=wrap;rounded=0;fillColor=none;"
            "strokeColor=none;align=center;verticalAlign=middle;"
            "fontSize=14;fontColor=#1F2937;" + style
        ),
        "vertex": "1",
        "parent": parent
    })
    geo = SubElement(root[-1], "mxGeometry", {
        "x": str(x), "y": str(y), "width": str(w), "height": str(h), "as": "geometry"
    })
    return cell_id

def add_box(title, body, x, y, w, h, fill="#FFFFFF", stroke="#2563EB",
            title_fill=None, font_size=13, parent="1"):
    cell_id = new_id("box")
    if title_fill is None:
        title_fill = stroke

    html = (
        f"<div style='font-size:{font_size}px;font-weight:bold;color:#FFFFFF;"
        f"background:{title_fill};padding:7px;border-radius:7px 7px 0 0'>"
        f"{escape(title)}</div>"
        f"<div style='font-size:{font_size-1}px;color:#111827;padding:8px;"
        f"text-align:left;line-height:1.35'>{body}</div>"
    )

    style = (
        "rounded=1;whiteSpace=wrap;html=1;fillColor=" + fill +
        ";strokeColor=" + stroke + ";strokeWidth=2;"
        "shadow=1;arcSize=12;align=left;verticalAlign=top;"
    )

    cell = SubElement(root, "mxCell", {
        "id": cell_id,
        "value": html,
        "style": style,
        "vertex": "1",
        "parent": parent
    })
    SubElement(cell, "mxGeometry", {
        "x": str(x), "y": str(y), "width": str(w), "height": str(h), "as": "geometry"
    })
    return cell_id

def add_section(title, x, y, w, h, fill, stroke, title_h=38):
    cell_id = new_id("section")
    html = (
        f"<div style='font-size:15px;font-weight:bold;color:#FFFFFF;"
        f"background:{stroke};padding:9px;text-align:left'>"
        f"{escape(title)}</div>"
    )
    cell = SubElement(root, "mxCell", {
        "id": cell_id,
        "value": html,
        "style": (
            f"rounded=1;whiteSpace=wrap;html=1;fillColor={fill};"
            f"strokeColor={stroke};strokeWidth=2;shadow=1;arcSize=10;"
            "align=left;verticalAlign=top;"
        ),
        "vertex": "1",
        "parent": "1"
    })
    SubElement(cell, "mxGeometry", {
        "x": str(x), "y": str(y), "width": str(w), "height": str(h), "as": "geometry"
    })
    return cell_id

def add_edge(source, target, color="#2563EB", width=2, dashed=False,
             exit_x=None, exit_y=None, entry_x=None, entry_y=None):
    edge_id = new_id("edge")
    style = (
        f"edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;"
        f"jettySize=auto;html=1;strokeColor={color};strokeWidth={width};"
        "endArrow=block;endFill=1;"
    )
    if dashed:
        style += "dashed=1;dashPattern=6 6;"
    if exit_x is not None:
        style += f"exitX={exit_x};exitY={exit_y};exitDx=0;exitDy=0;"
    if entry_x is not None:
        style += f"entryX={entry_x};entryY={entry_y};entryDx=0;entryDy=0;"

    cell = SubElement(root, "mxCell", {
        "id": edge_id,
        "value": "",
        "style": style,
        "edge": "1",
        "parent": "1",
        "source": source,
        "target": target
    })
    SubElement(cell, "mxGeometry", {"relative": "1", "as": "geometry"})
    return edge_id

def add_database(title, body, x, y, w, h, stroke="#0F5CAD"):
    cell_id = new_id("db")
    html = (
        f"<div style='font-size:13px;font-weight:bold;color:#FFFFFF;"
        f"background:{stroke};padding:7px;text-align:center'>"
        f"{escape(title)}</div>"
        f"<div style='font-size:12px;color:#111827;padding:10px;text-align:center'>"
        f"{body}</div>"
    )
    cell = SubElement(root, "mxCell", {
        "id": cell_id,
        "value": html,
        "style": (
            "shape=cylinder;whiteSpace=wrap;html=1;boundedLbl=1;"
            f"fillColor=#DCEEFF;strokeColor={stroke};strokeWidth=2;"
            "fontColor=#111827;shadow=1;"
        ),
        "vertex": "1",
        "parent": "1"
    })
    SubElement(cell, "mxGeometry", {
        "x": str(x), "y": str(y), "width": str(w), "height": str(h), "as": "geometry"
    })
    return cell_id

# ------------------------------------------------------------
# Title
# ------------------------------------------------------------
add_text(
    "CarePath - System Architecture",
    30, 20, 1540, 50,
    "fontSize=28;fontStyle=1;fontColor=#111827;align=left;"
)

# ------------------------------------------------------------
# 1. Data Sources
# ------------------------------------------------------------
s1 = add_section("1. DATA SOURCES", 30, 90, 230, 250, "#EAF3FF", "#075985")
b1 = add_box(
    "Source Systems",
    "📄 Claims Data<br>👥 Beneficiary Data<br>🩺 Diagnosis Codes<br>🔧 Procedure Codes<br>🏥 Provider / Hospital Data",
    45, 145, 200, 170, "#FFFFFF", "#075985", "#075985", 13
)

# ------------------------------------------------------------
# 2. Data Engineering & ETL
# ------------------------------------------------------------
s2 = add_section("2. DATA ENGINEERING & ETL", 290, 90, 250, 250, "#EAF3FF", "#0284C7")
b2 = add_box(
    "DATA ENGINEERING & ETL PROCESS",
    "🧹 Data Cleaning<br>🧹 Deduplication<br>⇆ Standardization<br>🏷 Claim Classification<br>🔎 Feature Extraction<br>🧭 Patient Journey Events<br><br>⚙️",
    305, 145, 220, 170, "#FFFFFF", "#0284C7", "#0284C7", 12
)

# ------------------------------------------------------------
# 3. Master Dataset
# ------------------------------------------------------------
s3 = add_section("3. MASTER DATASET", 570, 90, 220, 250, "#EAF3FF", "#075985")
b3 = add_database(
    "Unified Patient Dataset",
    "<b>Longitudinal</b><br>Patient<br>Care Journey<br><br>Claims + Events + Features",
    600, 155, 160, 145, "#075985"
)

# ------------------------------------------------------------
# 4. ML Pipeline
# ------------------------------------------------------------
s4 = add_section("4. ML PIPELINE", 820, 90, 300, 330, "#FFF3E6", "#D97706")
b4 = add_box(
    "Feature Engineering",
    "• Temporal + Trajectory Features<br><br>"
    "<b>Feature Selection</b><br><br>"
    "<b>Model Training</b><br>"
    "Logistic Regression &nbsp; Random Forest &nbsp; XGBoost<br><br>"
    "↓ Ensemble / Stacking",
    835, 145, 270, 245, "#FFFDF8", "#D97706", "#D97706", 12
)

# ------------------------------------------------------------
# 5. Model Outputs
# ------------------------------------------------------------
s5 = add_section("5. MODEL OUTPUTS", 1150, 90, 250, 300, "#EEF6FF", "#0369A1")
b5 = add_box(
    "Risk & Explainability",
    "• Risk Score (0–100)<br>• Risk Level (Low / Medium / High)<br>• Top Risk Factors<br>• Explanation (Feature Importance)<br>• Prediction History",
    1165, 145, 220, 205, "#FFFFFF", "#0369A1", "#0369A1", 13
)

# ------------------------------------------------------------
# LLM
# ------------------------------------------------------------
llm = add_box(
    "LLM (Groq)",
    "🧠 Clinical Reasoning<br>• Care Journey Audit<br>• Member Necessity Analysis<br>• Communication Generation<br><br>"
    "<b>Model:</b><br>openai/gpt-oss-20b",
    1430, 90, 140, 300, "#F4EEFF", "#7C3AED", "#4C1D95", 11
)

# ------------------------------------------------------------
# 6. Backend
# ------------------------------------------------------------
s6 = add_section("6. BACKEND (FastAPI)", 540, 460, 610, 245, "#EAF3FF", "#0F3B82")
b6 = add_box(
    "API Layer",
    "Patient APIs (CRUD) &nbsp; | &nbsp; Risk Prediction API &nbsp; | &nbsp; Risk Ranking API<br>"
    "Explanation API &nbsp; | &nbsp; Patient Journey API<br><br>"
    "Report Upload API &nbsp; | &nbsp; Appointment API &nbsp; | &nbsp; Alerts & Notifications<br>"
    "Financial/Finpact Analysis &nbsp; | &nbsp; Insurance/Member Analysis<br><br>"
    "<div style='background:#1479E8;color:white;padding:8px;text-align:center'>"
    "<b>Auth, Validation, Error Handling, Logging</b></div>",
    555, 505, 580, 180, "#FFFFFF", "#0F3B82", "#0F3B82", 11
)

# ------------------------------------------------------------
# 7. Database
# ------------------------------------------------------------
s7 = add_section("7. DATABASE", 1180, 460, 220, 245, "#EAF3FF", "#075985")
b7 = add_database(
    "PostgreSQL (Production)<br>or<br>SQLite (Development)",
    "Patients<br>Journey Events<br>Feature Snapshots<br>Predictions<br>Alerts<br>Notifications<br>Appointments<br>Reports<br>Financial Data<br>Insurance Data",
    1205, 515, 170, 165, "#075985"
)

# ------------------------------------------------------------
# 8. Frontend
# ------------------------------------------------------------
s8 = add_section("8. FRONTEND (Next.js + React)", 30, 460, 450, 310, "#EAF3FF", "#075985")
b8 = add_box(
    "Hospital / Care Management View",
    "• Patient Dashboard<br>• Patient Table<br>• Patient Detail<br>• Journey Timeline<br>• Risk Visualization<br>• Alerts & Notifications<br>• Reports & Appointments<br><br>"
    "<b>Insurance / Member View</b><br>• Member Dashboard<br>• Member Table<br>• Member Detail<br>• Risk & Impact View<br>• Financial Analysis<br>• Utilization Trends<br>• Alerts & Communication",
    45, 515, 420, 235, "#FFFFFF", "#075985", "#075985", 12
)

# ------------------------------------------------------------
# 9. Integrations
# ------------------------------------------------------------
s9 = add_section("9. INTEGRATIONS", 1430, 460, 140, 245, "#F4EEFF", "#7C3AED")
b9 = add_box(
    "External Services",
    "🧠 Groq LLM API<br><br>✉ Email / SMS Service<br><br>📁 File Storage (Reports)<br><br>🏥 External EHR<br><br>☁ Cloud / Deployment",
    1440, 515, 120, 170, "#FFFFFF", "#7C3AED", "#4C1D95", 10
)

# ------------------------------------------------------------
# 10. Alerts & Interventions
# ------------------------------------------------------------
s10 = add_section("10. ALERTS & INTERVENTIONS", 540, 735, 610, 120, "#FFF3E6", "#D97706")
b10 = add_box(
    "Care Management Actions",
    "🔔 High Risk Alerts &nbsp;&nbsp;&nbsp; ✉ Recommended Interventions &nbsp;&nbsp;&nbsp; "
    "✉ Care Manager Notifications &nbsp;&nbsp;&nbsp; 📈 Impact Tracking",
    555, 785, 580, 55, "#FFFDF8", "#D97706", "#D97706", 11
)

# ------------------------------------------------------------
# 11. Users / Stakeholders
# ------------------------------------------------------------
s11 = add_section("11. USERS / STAKEHOLDERS", 350, 885, 1050, 90, "#EAF3FF", "#075985")
b11 = add_box(
    "Stakeholders",
    "👤 Care Managers &nbsp;&nbsp; 👨‍⚕ Doctors &nbsp;&nbsp; 👤 Hospital Admin &nbsp;&nbsp; "
    "👤 Insurance Analysts &nbsp;&nbsp; 👤 Case Managers &nbsp;&nbsp; 👥 Patients / Members",
    365, 925, 1020, 35, "#FFFFFF", "#075985", "#075985", 10
)

# ------------------------------------------------------------
# Connections
# ------------------------------------------------------------
add_edge(b1, b2, "#0F6CBD", 2)
add_edge(b2, b3, "#0F6CBD", 2)
add_edge(b3, b4, "#0F6CBD", 2)
add_edge(b4, b5, "#D97706", 2)
add_edge(b5, llm, "#7C3AED", 2)

add_edge(b5, b6, "#0F6CBD", 2)
add_edge(b6, b7, "#0F6CBD", 2)
add_edge(b7, b9, "#7C3AED", 2)
add_edge(b6, b8, "#0F6CBD", 2)

add_edge(b6, b10, "#D97706", 2)
add_edge(b10, b11, "#D97706", 2)
add_edge(b11, b8, "#0F6CBD", 2)

add_edge(b9, b11, "#7C3AED", 2, dashed=True)
add_edge(b9, b6, "#7C3AED", 2)
add_edge(b11, b6, "#0F6CBD", 2, dashed=True)

# Feedback labels
add_text("New Patient Information", 80, 790, 170, 45,
         "fontSize=13;fontStyle=1;fontColor=#1F2937;")
add_text("Dynamic Risk Recalculation", 1220, 780, 210, 45,
         "fontSize=13;fontStyle=1;fontColor=#1F2937;")

# Add light background / footer note
add_text(
    "CarePath: AI-powered longitudinal patient risk prediction, explainability, care management and insurance intervention platform",
    30, 985, 1540, 25,
    "fontSize=11;fontColor=#64748B;align=left;"
)

# Write the .drawio file
ElementTree(mxfile).write(OUTPUT_FILE, encoding="utf-8", xml_declaration=True)

print(f"Created: {OUTPUT_FILE}")
