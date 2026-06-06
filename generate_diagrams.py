"""
Generates two PNG diagrams for the project:
  diagrams/architecture.png  — static component map of the codebase
  diagrams/workflow.png      — step-by-step runtime data-flow
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch

os.makedirs("diagrams", exist_ok=True)

# ── Shared palette ────────────────────────────────────────────────────────────

P = {
    "bg":           "#F8F9FA",
    "border_light": "#CCD1D9",
    # layer colours
    "ext_face":     "#D6EAF8", "ext_edge":    "#1F618D",
    "app_face":     "#EAFAF1", "app_edge":    "#1E8449",
    "route_face":   "#D5F5E3", "route_edge":  "#196F3D",
    "svc_face":     "#FEF5E7", "svc_edge":    "#D35400",
    "data_face":    "#F4ECF7", "data_edge":   "#7D3C98",
    "db_face":      "#EBF5FB", "db_edge":     "#2471A3",
    "arrow":        "#2C3E50",
    "title":        "#17202A",
    "label":        "#1A252F",
    "sub":          "#5D6D7E",
    "white":        "#FFFFFF",
    # workflow step colours
    "w_input":      ("#D6EAF8", "#1F618D"),
    "w_validate":   ("#FDEBD0", "#A04000"),
    "w_store":      ("#F4ECF7", "#7D3C98"),
    "w_lookup":     ("#D1F2EB", "#0E6655"),
    "w_ai":         ("#D5F5E3", "#1E8449"),
    "w_parse":      ("#FEF9E7", "#9A7D0A"),
    "w_route":      ("#EBF5FB", "#1A5276"),
    "w_notify":     ("#FEF5E7", "#D35400"),
    "w_output":     ("#D6EAF8", "#1F618D"),
}


# ── Low-level drawing helpers ─────────────────────────────────────────────────

def rbox(ax, cx, cy, w, h, text, sub=None,
         fc="#D6EAF8", ec="#1F618D", fs=10, fw="bold",
         text_color="#1A252F", zorder=3):
    patch = FancyBboxPatch(
        (cx - w / 2, cy - h / 2), w, h,
        boxstyle="round,pad=0.07",
        facecolor=fc, edgecolor=ec, linewidth=1.8, zorder=zorder,
    )
    ax.add_patch(patch)
    if sub:
        ax.text(cx, cy + h * 0.16, text, ha="center", va="center",
                fontsize=fs, fontweight=fw, color=text_color, zorder=zorder + 1)
        ax.text(cx, cy - h * 0.2, sub, ha="center", va="center",
                fontsize=max(fs - 1.5, 7), color=P["sub"], zorder=zorder + 1,
                style="italic")
    else:
        ax.text(cx, cy, text, ha="center", va="center",
                fontsize=fs, fontweight=fw, color=text_color, zorder=zorder + 1)


def arrow(ax, x1, y1, x2, y2, color=None, lw=1.6,
          dashed=False, label=None, rad=0.0):
    color = color or P["arrow"]
    ls = (0, (4, 3)) if dashed else "solid"
    ax.annotate(
        "", xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(
            arrowstyle="-|>", color=color, lw=lw,
            mutation_scale=13, linestyle=ls,
            connectionstyle=f"arc3,rad={rad}",
        ),
        zorder=5,
    )
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mx + 0.1, my, label, fontsize=7.5,
                color=color, va="center", zorder=6)


def badge(ax, cx, cy, r, text, fc="#1F618D"):
    circle = plt.Circle((cx, cy), r, color=fc, zorder=6)
    ax.add_patch(circle)
    ax.text(cx, cy, text, ha="center", va="center",
            fontsize=8, fontweight="bold", color="white", zorder=7)


def section_label(ax, x, y, text, color="#5D6D7E"):
    ax.text(x, y, text, fontsize=8, color=color,
            fontstyle="italic", va="center", zorder=4)


# ─────────────────────────────────────────────────────────────────────────────
#  DIAGRAM 1 — System Architecture
# ─────────────────────────────────────────────────────────────────────────────

def build_architecture():
    fig, ax = plt.subplots(figsize=(17, 11))
    fig.patch.set_facecolor(P["bg"])
    ax.set_facecolor(P["bg"])
    ax.set_xlim(0, 17)
    ax.set_ylim(0, 11)
    ax.axis("off")

    # ── Title ──────────────────────────────────────────────────────────────
    ax.text(8.5, 10.55, "AI Customer Support Agent — System Architecture",
            ha="center", va="center", fontsize=15, fontweight="bold",
            color=P["title"])
    ax.text(8.5, 10.15, "Component map: modules, layers, and external dependencies",
            ha="center", va="center", fontsize=10, color=P["sub"])

    # ── External systems ───────────────────────────────────────────────────
    rbox(ax, 2.5, 9.2, 3.8, 0.95, "HTTP Client",
         sub="curl / Postman / any REST client",
         fc=P["ext_face"], ec=P["ext_edge"], fs=10)

    rbox(ax, 14.3, 9.2, 3.8, 0.95, "OpenAI API",
         sub="gpt-4o-mini  ·  json_object mode",
         fc=P["ext_face"], ec=P["ext_edge"], fs=10)

    # ── FastAPI app container ──────────────────────────────────────────────
    app_box = FancyBboxPatch(
        (0.4, 1.2), 13.4, 7.45,
        boxstyle="round,pad=0.12",
        facecolor=P["app_face"], edgecolor=P["app_edge"],
        linewidth=2.2, zorder=1, linestyle="--",
    )
    ax.add_patch(app_box)
    ax.text(0.75, 8.53, "FastAPI Application  (app/)",
            fontsize=9, color=P["app_edge"], fontweight="bold",
            va="center", zorder=2)

    # ── Routes layer ──────────────────────────────────────────────────────
    rbox(ax, 7.1, 7.9, 12.2, 0.85, "app/routes/tickets.py  — Route Handlers",
         sub="GET /health   ·   POST /tickets   ·   GET /tickets   ·   GET /tickets/{id}",
         fc=P["route_face"], ec=P["route_edge"], fs=10, zorder=3)

    # ── Services layer ────────────────────────────────────────────────────
    SVC_Y = 6.35
    svc_data = [
        (1.95,  "ai_service.py",          "analyze_ticket()\nparse_ai_response()"),
        (5.4,   "routing_service.py",      "route_ticket()"),
        (8.5,   "notification_service.py", "send_notification()"),
        (11.6,  "customer_lookup.py",      "lookup_customer()"),
    ]
    for sx, title, sub in svc_data:
        rbox(ax, sx, SVC_Y, 2.9, 1.3, title, sub=sub,
             fc=P["svc_face"], ec=P["svc_edge"], fs=8.5, zorder=3)

    # ── Data layer ────────────────────────────────────────────────────────
    DATA_Y = 4.55
    rbox(ax, 3.55, DATA_Y, 5.7, 1.55, "app/schemas/",
         sub="TicketCreate  ·  TicketResponse\nTicketDetail  ·  AnalysisResponse\n(Pydantic v2  —  validation + serialisation)",
         fc=P["data_face"], ec=P["data_edge"], fs=8.5, zorder=3)

    rbox(ax, 10.3, DATA_Y, 5.7, 1.55, "app/models/",
         sub="Ticket   ←—one-to-one—→   TicketAnalysis\n(SQLAlchemy 2.0 ORM)\napp/database.py  ·  SessionLocal",
         fc=P["data_face"], ec=P["data_edge"], fs=8.5, zorder=3)

    # ── Entry point label ────────────────────────────────────────────────
    rbox(ax, 7.1, 2.75, 5.4, 0.9, "app/main.py",
         sub="load_dotenv()  ·  create_all()  ·  FastAPI()",
         fc=P["app_face"], ec=P["app_edge"], fs=9, zorder=3)

    # ── SQLite database ───────────────────────────────────────────────────
    rbox(ax, 3.9, 0.65, 5.5, 0.85, "SQLite   (support.db)",
         sub="tables: tickets  ·  ticket_analyses",
         fc=P["db_face"], ec=P["db_edge"], fs=10, zorder=3)

    # ── Arrows ────────────────────────────────────────────────────────────

    # HTTP client → Routes
    arrow(ax, 2.5, 8.72, 2.5, 8.33, color=P["ext_edge"])
    ax.text(2.75, 8.52, "HTTP", fontsize=7.5, color=P["ext_edge"], va="center")

    # Routes → ai_service (down)
    arrow(ax, 4.5, 7.48, 2.4, 7.01, color=P["route_edge"])
    # Routes → routing
    arrow(ax, 5.6, 7.48, 5.4, 7.01, color=P["route_edge"])
    # Routes → notification
    arrow(ax, 7.1, 7.48, 8.5, 7.01, color=P["route_edge"])
    # Routes → customer_lookup
    arrow(ax, 8.7, 7.48, 11.5, 7.01, color=P["route_edge"])

    # ai_service → OpenAI (curved)
    arrow(ax, 3.3, 6.52, 12.4, 8.72, color=P["ext_edge"],
          dashed=True, label="HTTPS / JSON", rad=-0.2)

    # Services → schemas
    arrow(ax, 2.0, 5.7,  3.55, 5.33, color=P["data_edge"])
    arrow(ax, 5.4, 5.7,  4.6,  5.33, color=P["data_edge"])

    # Services → models
    arrow(ax, 8.5, 5.7,  10.3, 5.33, color=P["data_edge"])
    arrow(ax, 11.6,5.7,  11.2, 5.33, color=P["data_edge"])

    # models → SQLite
    arrow(ax, 7.5, 3.78, 4.5, 1.08, color=P["db_edge"])
    ax.text(6.5, 2.35, "SQLAlchemy", fontsize=7.5,
            color=P["db_edge"], va="center", rotation=32)

    # main.py → Routes (startup wiring)
    arrow(ax, 7.1, 3.2, 7.1, 8.33 - 5.56, color=P["app_edge"],
          dashed=True, label="include_router()", rad=0.0)

    # ── Legend ────────────────────────────────────────────────────────────
    legend_items = [
        mpatches.Patch(fc=P["ext_face"],   ec=P["ext_edge"],   label="External System"),
        mpatches.Patch(fc=P["route_face"], ec=P["route_edge"], label="Route Layer"),
        mpatches.Patch(fc=P["svc_face"],   ec=P["svc_edge"],   label="Service Layer"),
        mpatches.Patch(fc=P["data_face"],  ec=P["data_edge"],  label="Data / Schema Layer"),
        mpatches.Patch(fc=P["db_face"],    ec=P["db_edge"],    label="Database"),
    ]
    ax.legend(handles=legend_items, loc="lower right",
              fontsize=8.5, framealpha=0.9, edgecolor=P["border_light"],
              bbox_to_anchor=(0.995, 0.01))

    fig.tight_layout(pad=0.6)
    path = "diagrams/architecture.png"
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=P["bg"])
    plt.close(fig)
    print(f"  Saved: {path}")


# ─────────────────────────────────────────────────────────────────────────────
#  DIAGRAM 2 — Ticket Processing Workflow
# ─────────────────────────────────────────────────────────────────────────────

def build_workflow():
    fig, ax = plt.subplots(figsize=(10, 16))
    fig.patch.set_facecolor(P["bg"])
    ax.set_facecolor(P["bg"])
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 16)
    ax.axis("off")

    # ── Title ──────────────────────────────────────────────────────────────
    ax.text(5.0, 15.55, "Ticket Processing Workflow",
            ha="center", va="center", fontsize=15, fontweight="bold",
            color=P["title"])
    ax.text(5.0, 15.15, "POST /tickets  —  end-to-end data-flow",
            ha="center", va="center", fontsize=10, color=P["sub"])

    # ── Steps ─────────────────────────────────────────────────────────────
    # (step_num, y_center, title, subtitle, face_color, edge_color, side_note)
    steps = [
        ( 1, 14.1,  "Customer Request",
          "POST /tickets  ·  JSON payload",
          *P["w_input"], None),
        ( 2, 12.75, "Input Validation",
          "Pydantic — email, min_length(1), required fields",
          *P["w_validate"], None),
        ( 3, 11.4,  "Store Ticket",
          "INSERT INTO tickets  ·  db.commit()  ·  db.refresh()",
          *P["w_store"], "SQLite"),
        ( 4, 10.05, "Customer Lookup",
          "lookup_customer(email)  ·  returns plan + status",
          *P["w_lookup"], "Mock DB"),
        ( 5,  8.7,  "OpenAI Analysis",
          "gpt-4o-mini  ·  json_object  ·  temperature=0.1",
          *P["w_ai"], "OpenAI API"),
        ( 6,  7.35, "Parse AI Response",
          "parse_ai_response()  ·  direct / markdown / regex",
          *P["w_parse"], None),
        ( 7,  6.0,  "Route to Team",
          "route_ticket(category)  ·  deterministic mapping",
          *P["w_route"], None),
        ( 8,  4.65, "Store Analysis",
          "INSERT INTO ticket_analyses  ·  FK → ticket.id",
          *P["w_store"], "SQLite"),
        ( 9,  3.3,  "Send Notification",
          "send_notification()  ·  formatted stdout log",
          *P["w_notify"], None),
        (10,  1.95, "Return JSON Response",
          "ticket_id · category · priority · assigned_team · draft",
          *P["w_output"], None),
    ]

    BOX_W = 6.4
    BOX_H = 0.82
    CX    = 5.0
    BADGE_X = CX - BOX_W / 2 - 0.55

    for num, cy, title, sub, fc, ec, note in steps:
        # numbered badge
        badge(ax, BADGE_X, cy, 0.28, str(num), fc=ec)

        # main box
        rbox(ax, CX, cy, BOX_W, BOX_H, title, sub=sub,
             fc=fc, ec=ec, fs=11, zorder=3)

        # side annotation (e.g. "SQLite", "OpenAI API")
        if note:
            note_x = CX + BOX_W / 2 + 0.15
            note_box = FancyBboxPatch(
                (note_x, cy - 0.22), 1.3, 0.44,
                boxstyle="round,pad=0.05",
                facecolor=fc, edgecolor=ec,
                linewidth=1.2, zorder=3,
            )
            ax.add_patch(note_box)
            ax.text(note_x + 0.65, cy, note,
                    ha="center", va="center", fontsize=8,
                    fontweight="bold", color=ec, zorder=4)
            ax.annotate("", xy=(note_x, cy),
                        xytext=(CX + BOX_W / 2, cy),
                        arrowprops=dict(
                            arrowstyle="<-", color=ec, lw=1.2,
                            linestyle=(0, (3, 2)), mutation_scale=10,
                        ), zorder=5)

    # ── Vertical arrows between steps ─────────────────────────────────────
    for i in range(len(steps) - 1):
        _, y_curr = steps[i][0], steps[i][1]
        _, y_next = steps[i + 1][0], steps[i + 1][1]
        top    = y_curr - BOX_H / 2 - 0.04
        bottom = y_next + BOX_H / 2 + 0.04
        arrow(ax, CX, top, CX, bottom, color=P["arrow"], lw=2.0)

    # ── Legend ────────────────────────────────────────────────────────────
    legend_items = [
        mpatches.Patch(fc=P["w_input"][0],    ec=P["w_input"][1],    label="I/O (request & response)"),
        mpatches.Patch(fc=P["w_validate"][0], ec=P["w_validate"][1], label="Validation"),
        mpatches.Patch(fc=P["w_store"][0],    ec=P["w_store"][1],    label="Database write"),
        mpatches.Patch(fc=P["w_lookup"][0],   ec=P["w_lookup"][1],   label="External lookup"),
        mpatches.Patch(fc=P["w_ai"][0],       ec=P["w_ai"][1],       label="AI processing"),
        mpatches.Patch(fc=P["w_parse"][0],    ec=P["w_parse"][1],    label="Parsing / logic"),
        mpatches.Patch(fc=P["w_route"][0],    ec=P["w_route"][1],    label="Routing"),
        mpatches.Patch(fc=P["w_notify"][0],   ec=P["w_notify"][1],   label="Notification"),
    ]
    ax.legend(handles=legend_items, loc="lower right",
              fontsize=8, framealpha=0.9, edgecolor=P["border_light"],
              bbox_to_anchor=(0.99, 0.01), ncol=2)

    fig.tight_layout(pad=0.6)
    path = "diagrams/workflow.png"
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=P["bg"])
    plt.close(fig)
    print(f"  Saved: {path}")


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Generating diagrams...")
    build_architecture()
    build_workflow()
    print("Done.")
