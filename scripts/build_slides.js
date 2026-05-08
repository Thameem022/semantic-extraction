const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.title = "Semantic Extraction: Accuracy Evaluation";

// ── Color palette ────────────────────────────────────────────────────────────
const NAVY   = "1E2761";   // dominant dark
const BLUE   = "2D4A9F";   // supporting blue
const ICE    = "CADCFC";   // light accent
const WHITE  = "FFFFFF";
const GRAY   = "F4F6FA";   // slide background (content slides)
const TEXT   = "1A2340";   // body text
const MUTED  = "64748B";
const GREEN  = "16A34A";
const RED    = "DC2626";
const AMBER  = "D97706";

// ── Helpers ──────────────────────────────────────────────────────────────────
function makeShadow() {
  return { type: "outer", color: "000000", opacity: 0.10, blur: 6, offset: 3, angle: 135 };
}

function sectionHeader(slide, title) {
  // Pill-shaped accent + title text (no underline bar)
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.45, y: 0.22, w: 0.06, h: 0.50,
    fill: { color: ICE }, line: { color: ICE }
  });
  slide.addText(title, {
    x: 0.60, y: 0.16, w: 8.8, h: 0.60,
    fontSize: 26, bold: true, color: NAVY, fontFace: "Georgia",
    margin: 0, valign: "middle"
  });
}

function statCard(slide, x, y, w, h, value, label, color) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w, h, fill: { color: WHITE },
    shadow: makeShadow(), line: { color: "E2E8F0", pt: 1 }
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w, h: 0.06, fill: { color }, line: { color }
  });
  slide.addText(value, {
    x: x + 0.1, y: y + 0.10, w: w - 0.2, h: h * 0.55,
    fontSize: 36, bold: true, color, align: "center", fontFace: "Georgia", margin: 0
  });
  slide.addText(label, {
    x: x + 0.1, y: y + h * 0.62, w: w - 0.2, h: h * 0.38,
    fontSize: 11, color: MUTED, align: "center", fontFace: "Calibri", margin: 0
  });
}

// ── SLIDE 1 — Title ──────────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: NAVY };

  // Subtle geometric accent — two overlapping rectangles
  s.addShape(pres.shapes.RECTANGLE, {
    x: 7.2, y: 0, w: 2.8, h: 5.625,
    fill: { color: BLUE, transparency: 60 }, line: { color: BLUE, transparency: 60 }
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 8.5, y: 0, w: 1.5, h: 5.625,
    fill: { color: ICE, transparency: 75 }, line: { color: ICE, transparency: 75 }
  });

  // Tag line
  s.addText("BMP2 PROJECT  ·  SPRING 2026", {
    x: 0.6, y: 1.10, w: 6.8, h: 0.35,
    fontSize: 11, color: ICE, charSpacing: 4, fontFace: "Calibri", margin: 0
  });

  // Main title
  s.addText("Semantic Extraction", {
    x: 0.6, y: 1.55, w: 6.8, h: 0.80,
    fontSize: 42, bold: true, color: WHITE, fontFace: "Georgia", margin: 0
  });
  s.addText("Accuracy Evaluation", {
    x: 0.6, y: 2.30, w: 6.8, h: 0.75,
    fontSize: 38, bold: false, color: ICE, fontFace: "Georgia", margin: 0
  });

  // Divider line
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.6, y: 3.18, w: 2.2, h: 0.04,
    fill: { color: ICE }, line: { color: ICE }
  });

  // Sub-text
  s.addText("AI-powered field extraction from EPLI application PDFs\nEvaluated against a 20-document hand-labeled golden set", {
    x: 0.6, y: 3.35, w: 6.8, h: 0.90,
    fontSize: 13, color: "A8BFEF", fontFace: "Calibri", lineSpacingMultiple: 1.4, margin: 0
  });
}

// ── SLIDE 2 — Project Overview ───────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: GRAY };
  sectionHeader(s, "Project Overview");

  // Pipeline flow — 4 boxes with arrows
  const boxes = [
    { label: "EPLI Application\nPDFs", sub: "20 insurance\napplications", color: NAVY },
    { label: "Azure AI\nPipeline", sub: "OCR + LLM\nextraction", color: BLUE },
    { label: "Structured\nJSON Output", sub: "50+ fields\nper document", color: "1D5EA8" },
    { label: "Accuracy\nEvaluation", sub: "vs. hand-labeled\ngolden set", color: GREEN },
  ];

  const bw = 1.85, bh = 1.30, gap = 0.22, startX = 0.45, bY = 1.50;
  boxes.forEach((b, i) => {
    const x = startX + i * (bw + gap + 0.18);
    s.addShape(pres.shapes.RECTANGLE, {
      x, y: bY, w: bw, h: bh,
      fill: { color: b.color }, shadow: makeShadow(), line: { color: b.color }
    });
    s.addText(b.label, {
      x: x + 0.08, y: bY + 0.08, w: bw - 0.16, h: 0.72,
      fontSize: 13, bold: true, color: WHITE, align: "center", fontFace: "Georgia",
      valign: "middle", margin: 0
    });
    s.addText(b.sub, {
      x: x + 0.08, y: bY + 0.80, w: bw - 0.16, h: 0.44,
      fontSize: 10, color: ICE, align: "center", fontFace: "Calibri", margin: 0
    });

    // Arrow between boxes
    if (i < boxes.length - 1) {
      const ax = x + bw + 0.04;
      s.addShape(pres.shapes.RECTANGLE, {
        x: ax, y: bY + bh / 2 - 0.025, w: 0.30, h: 0.05,
        fill: { color: MUTED }, line: { color: MUTED }
      });
      // Arrow head (triangle approximated with narrow rectangle)
      s.addShape(pres.shapes.RECTANGLE, {
        x: ax + 0.24, y: bY + bh / 2 - 0.07, w: 0.07, h: 0.14,
        fill: { color: MUTED }, line: { color: MUTED }
      });
    }
  });

  // Key stats row
  const stats = [
    { v: "20", l: "PDF Documents\nEvaluated" },
    { v: "50+", l: "Fields Extracted\nPer Document" },
    { v: "5", l: "Sections\nAssessed" },
    { v: "493", l: "Total Scorable\nField Instances" },
  ];
  stats.forEach((st, i) => {
    statCard(s, 0.45 + i * 2.37, 3.22, 2.10, 1.62, st.v, st.l, NAVY);
  });
}

// ── SLIDE 3 — Fields to Extract: Overview (JSON candidate reference) ─────────
{
  const s = pres.addSlide();
  s.background = { color: GRAY };
  sectionHeader(s, "Data Elements to Extract — Overview");

  // Source badge
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.45, y: 0.84, w: 2.50, h: 0.28,
    fill: { color: NAVY }, line: { color: NAVY }
  });
  s.addText("📄  Chubb_App.pdf  (example candidate)", {
    x: 0.55, y: 0.84, w: 2.40, h: 0.28,
    fontSize: 8, color: ICE, fontFace: "Calibri", valign: "middle", margin: 0
  });

  // Legend
  const legend = [
    { label: "string", color: "86EFAC" },
    { label: "number", color: "FCD34D" },
    { label: "boolean", color: "60A5FA" },
    { label: "null", color: "64748B" },
  ];
  legend.forEach((l, li) => {
    const lx = 6.30 + li * 0.72;
    s.addShape(pres.shapes.OVAL, { x: lx, y: 0.90, w: 0.12, h: 0.12, fill: { color: l.color }, line: { color: l.color } });
    s.addText(l.label, { x: lx + 0.16, y: 0.86, w: 0.56, h: 0.22, fontSize: 7.5, color: MUTED, fontFace: "Calibri", margin: 0 });
  });

  // ── helper: build rich-text lines from field array ──
  const KEY_C  = "94B4D1";
  const STR_C  = "86EFAC";
  const NULL_C = "64748B";
  const NUM_C  = "FCD34D";
  const BOOL_C = "60A5FA";
  const DIM_C  = "4A5568";

  function jLines(fields) {
    const runs = [];
    fields.forEach((f, fi) => {
      const isMore = f.type === "more";
      runs.push(
        { text: f.key, options: { color: isMore ? NULL_C : KEY_C, bold: false, italics: isMore } },
        { text: isMore ? "" : ": ", options: { color: DIM_C } },
        { text: f.val, options: {
            color: f.type === "string"  ? STR_C
                 : f.type === "number"  ? NUM_C
                 : f.type === "bool"    ? BOOL_C
                 : NULL_C,
            italics: isMore,
          }
        },
      );
      if (fi < fields.length - 1) runs.push({ text: "", options: { breakLine: true } });
    });
    return runs;
  }

  // Panel geometry — two rows
  // Row 1: GeneralInformation (w=3.80), CoverageDetails (w=2.52), RiskAssessment (w=2.33)
  // Row 2: EmployeeCategory (w=4.47), EPLISpecificQuestions (w=4.48)
  const R1Y = 1.20, R1H = 2.06;
  const R2Y = 3.40, R2H = 1.96;
  const DARK = "1A1F36";
  const HDR_H = 0.38;

  function panel(s, x, y, w, h, title, count, color, fields) {
    // Outer card
    s.addShape(pres.shapes.RECTANGLE, { x, y, w, h, fill: { color: WHITE }, shadow: makeShadow(), line: { color: "E2E8F0", pt: 1 } });
    // Colored header
    s.addShape(pres.shapes.RECTANGLE, { x, y, w, h: HDR_H, fill: { color }, line: { color } });
    s.addText(title, {
      x: x + 0.10, y: y + 0.02, w: w - 0.82, h: HDR_H - 0.04,
      fontSize: 10, bold: true, color: WHITE, fontFace: "Georgia", valign: "middle", margin: 0
    });
    // Field count badge
    s.addShape(pres.shapes.RECTANGLE, { x: x + w - 0.58, y: y + 0.07, w: 0.50, h: 0.24, fill: { color: WHITE, transparency: 20 }, line: { color: WHITE, transparency: 40 } });
    s.addText(count + " fields", {
      x: x + w - 0.58, y: y + 0.07, w: 0.50, h: 0.24,
      fontSize: 7.5, bold: true, color: WHITE, align: "center", fontFace: "Calibri", valign: "middle", margin: 0
    });
    // Dark code body
    s.addShape(pres.shapes.RECTANGLE, { x, y: y + HDR_H, w, h: h - HDR_H, fill: { color: DARK }, line: { color: DARK } });
    // JSON lines
    s.addText(jLines(fields), {
      x: x + 0.12, y: y + HDR_H + 0.08, w: w - 0.24, h: h - HDR_H - 0.12,
      fontFace: "Consolas", fontSize: 8, lineSpacingMultiple: 1.38, valign: "top", margin: 0
    });
  }

  // ── Section data (actual Chubb_App.pdf values) ──

  panel(s, 0.45, R1Y, 3.80, R1H, "General Information", "27", NAVY, [
    { key: "Applicant",               val: '"IS Partners LLC"',      type: "string" },
    { key: "Address_Street",          val: '"1668 Susquehann Rd"',   type: "string" },
    { key: "Address_City / State / Zip", val: '"Dresher" / "PA" / "19025"', type: "string" },
    { key: "NAICSCode",               val: "null",                   type: "null"   },
    { key: "NatureOfOperations",      val: '"Professional Services"',type: "string" },
    { key: "Contact_Name",            val: '"Matt Dvorin"',          type: "string" },
    { key: "Contact_Email",           val: '"mdvorin@ispartnersilc…"',type: "string"},
    { key: "OrganizationalStructure", val: "null",                   type: "null"   },
    { key: "TotalNumberOfEmployees",  val: "46",                     type: "number" },
    { key: "RequestedEffectiveDate",  val: '"10/30/2025"',           type: "string" },
    { key: "… +17 more fields",       val: "",                       type: "more"   },
  ]);

  panel(s, 4.40, R1Y, 2.52, R1H, "Coverage Details", "9", BLUE, [
    { key: "CoverageType",      val: '"Emp. Practices Liab."', type: "string" },
    { key: "LimitRequested",    val: "null",                   type: "null"   },
    { key: "RetentionRequested",val: "null",                   type: "null"   },
    { key: "SharedLimit",       val: "false",                  type: "bool"   },
    { key: "DutyToDefend",      val: "null",                   type: "null"   },
    { key: "CurrentLimit",      val: "null",                   type: "null"   },
    { key: "CurrentRetention",  val: "null",                   type: "null"   },
    { key: "CurrentPremium",    val: "null",                   type: "null"   },
    { key: "CurrentCarrier",    val: "null",                   type: "null"   },
  ]);

  panel(s, 7.07, R1Y, 2.48, R1H, "Risk Assessment", "2", "1D5EA8", [
    { key: "NoticeOfClaim",val: "null",  type: "null" },
    { key: "Explanation",  val: "null",  type: "null" },
    { key: "", val: "", type: "more" },
    { key: "→ Maps to one question", val: "", type: "more" },
    { key: "  in BMP portal but", val: "", type: "more" },
    { key: "  asked 3 different", val: "", type: "more" },
    { key: "  ways across forms", val: "", type: "more" },
    { key: "  (18 mo / 3 yr / table)", val: "", type: "more" },
  ]);

  panel(s, 0.45, R2Y, 4.47, R2H, "Employee Category", "17", AMBER, [
    { key: "FTEmployees_CurrentYearTotal",  val: "46",      type: "number" },
    { key: "FTEmployees_CurrentYearCA",     val: "0",       type: "number" },
    { key: "FTEmployees_PriorYearTotal",    val: "39",      type: "number" },
    { key: "PTEmployees_CurrentYearTotal",  val: "6",       type: "number" },
    { key: "IndepContractors_CurrentYear",  val: "0",       type: "number" },
    { key: "Volunteers_CurrentYearTotal",   val: "null",    type: "null"   },
    { key: "Top3States_State1",             val: '"PA"',    type: "string" },
    { key: "Top3States_State2 / State3",    val: "null",    type: "null"   },
    { key: "SalaryRanges_Gte125k",          val: '"32.00"', type: "string" },
    { key: "SalaryRanges_Lt125k",           val: '"84.00"', type: "string" },
    { key: "… +7 more fields",              val: "",        type: "more"   },
  ]);

  panel(s, 5.07, R2Y, 4.48, R2H, "EPLI Specific Questions", "10", RED, [
    { key: "WorkforceReduction_Impacted",       val: "null",  type: "null" },
    { key: "ConsultedOutsideCounsel",           val: "null",  type: "null" },
    { key: "ReviewedExemptNonExempt",           val: "null",  type: "null" },
    { key: "CompletedWageAndHourAudit",         val: "null",  type: "null" },
    { key: "EmploymentDisputeOver10k",          val: "null",  type: "null" },
    { key: "EEOCOrSimilarProceeding",           val: "true",  type: "bool" },
    { key: "CrisisExpenseCoverage",             val: "null",  type: "null" },
    { key: "WorkplaceViolenceExpenseCoverage",  val: "true",  type: "bool" },
    { key: "WageAndHourDefenseExpenses",        val: "null",  type: "null" },
    { key: "AdditionalDefenseExpenseLimit",     val: "null",  type: "null" },
  ]);
}

// ── SLIDE 4 — General Information Fields ────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: GRAY };
  sectionHeader(s, "Section 1 — General Information  (27 fields)");

  // 5 grouped clusters
  const groups = [
    {
      label: "Company Identity",
      color: NAVY,
      fields: ["Applicant", "Address – Street", "Address – City", "Address – State", "Address – Zip Code",
               "Applicant's Website", "NAICS Code", "Date of Formation", "Nature of Operations"],
    },
    {
      label: "Primary Contact",
      color: BLUE,
      fields: ["Contact – Name", "Contact – Title", "Contact – Telephone", "Contact – Email"],
    },
    {
      label: "Risk Mgmt Contact",
      color: "1D5EA8",
      fields: ["Risk Mgmt Contact – Name", "Risk Mgmt Contact – Title",
               "Risk Mgmt Contact – Telephone", "Risk Mgmt Contact – Email"],
    },
    {
      label: "Entity Details",
      color: AMBER,
      fields: ["Tax Status", "Organizational Structure", "Total Number of Locations",
               "Requested Effective Date"],
    },
    {
      label: "Employee Geography",
      color: RED,
      fields: ["Total Number of Employees", "Employees – U.S.", "Employees – California",
               "Employees – Canada", "Employees – Outside U.S. & CAN",
               "Countries of Operation Outside U.S."],
    },
  ];

  // Layout: two rows — top row 3 cards, bottom row 2 cards
  const layout = [
    { x: 0.45, y: 0.92 },
    { x: 3.57, y: 0.92 },
    { x: 6.70, y: 0.92 },
    { x: 0.45, y: 3.08 },
    { x: 5.15, y: 3.08 },
  ];
  const cardW = [2.90, 2.90, 2.90, 4.45, 4.45];
  const cardH = 1.94;

  groups.forEach((g, i) => {
    const { x, y } = layout[i];
    const w = cardW[i];

    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w, h: cardH,
      fill: { color: WHITE }, shadow: makeShadow(), line: { color: "E2E8F0", pt: 1 }
    });
    // Header strip
    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w, h: 0.42,
      fill: { color: g.color }, line: { color: g.color }
    });
    s.addText(g.label, {
      x: x + 0.10, y: y + 0.04, w: w - 0.20, h: 0.34,
      fontSize: 11, bold: true, color: WHITE, fontFace: "Georgia",
      valign: "middle", margin: 0
    });
    // Fields as wrapped chips
    const chunkSize = i >= 3 ? 3 : 2;
    let lineY = y + 0.52;
    for (let r = 0; r < g.fields.length; r += chunkSize) {
      const row = g.fields.slice(r, r + chunkSize);
      const chipW = (w - 0.20 - (row.length - 1) * 0.08) / row.length;
      row.forEach((field, ci) => {
        const cx = x + 0.10 + ci * (chipW + 0.08);
        s.addShape(pres.shapes.RECTANGLE, {
          x: cx, y: lineY, w: chipW, h: 0.30,
          fill: { color: GRAY }, line: { color: "E2E8F0", pt: 1 }
        });
        s.addText(field, {
          x: cx + 0.04, y: lineY, w: chipW - 0.08, h: 0.30,
          fontSize: 8, color: TEXT, fontFace: "Calibri",
          valign: "middle", margin: 0
        });
      });
      lineY += 0.36;
    }
  });
}

// ── SLIDE 5 — Coverage Details + Risk Assessment ─────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: GRAY };
  sectionHeader(s, "Sections 2 & 3 — Coverage Details and Risk Assessment");

  // ── Coverage Details ──
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.45, y: 0.90, w: 9.10, h: 0.44,
    fill: { color: BLUE }, line: { color: BLUE }
  });
  s.addText("Section 2 — Coverage Details", {
    x: 0.60, y: 0.90, w: 9.00, h: 0.44,
    fontSize: 13, bold: true, color: WHITE, fontFace: "Georgia", valign: "middle", margin: 0
  });

  // Coverage table
  const covHeaders = ["Coverage Type", "Limit\nRequested", "Retention\nRequested", "Shared\nLimit",
                      "Duty to\nDefend", "Current\nLimit", "Current\nRetention", "Current\nPremium", "Current\nCarrier"];
  const covColW = [1.90, 0.90, 0.90, 0.76, 0.82, 0.90, 0.90, 0.90, 0.90];
  const covTableW = covColW.reduce((a, b) => a + b, 0);

  const covData = [
    covHeaders.map((h, hi) => ({
      text: h,
      options: { bold: true, color: WHITE, fill: { color: NAVY }, fontSize: 9, align: "center", valign: "middle" }
    })),
    [
      { text: "Employment Practices Liability", options: { fontSize: 9, color: TEXT, fill: { color: "EEF2FF" }, bold: true } },
      ...["$ amount", "$ amount", "Yes / No", "Duty / Non-duty", "$ amount", "$ amount", "$ amount", "Carrier name"].map(v => ({
        text: v,
        options: { fontSize: 8, color: MUTED, fill: { color: WHITE }, align: "center", italics: true }
      }))
    ]
  ];

  s.addTable(covData, {
    x: 0.45, y: 1.40, w: covTableW, colW: covColW,
    border: { pt: 0.5, color: "E2E8F0" }, rowH: 0.50,
  });

  // Callout note about Duty to Defend
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.45, y: 2.10, w: 9.10, h: 0.36,
    fill: { color: "EEF2FF" }, line: { color: ICE, pt: 1 }
  });
  s.addText("★  'Duty to Defend' is a key field — BMP portal expects 'Duty' or 'Non-duty', but forms often show a checkbox or the word 'selected'", {
    x: 0.60, y: 2.10, w: 8.80, h: 0.36,
    fontSize: 9, color: NAVY, fontFace: "Calibri", italics: true, valign: "middle", margin: 0
  });

  // ── Risk Assessment ──
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.45, y: 2.62, w: 9.10, h: 0.44,
    fill: { color: "1D5EA8" }, line: { color: "1D5EA8" }
  });
  s.addText("Section 3 — Risk Assessment", {
    x: 0.60, y: 2.62, w: 9.00, h: 0.44,
    fontSize: 13, bold: true, color: WHITE, fontFace: "Georgia", valign: "middle", margin: 0
  });

  const riskHeaders = ["Q#", "Question", "Past 18 Months", "Next 12 Months", "No (Neither)", "Explanation\nRequired", "Response Details"];
  const riskColW    = [0.40, 3.40, 1.12, 1.12, 1.00, 1.10, 1.96];

  const riskData = [
    riskHeaders.map(h => ({
      text: h,
      options: { bold: true, color: WHITE, fill: { color: "1D5EA8" }, fontSize: 9, align: "center", valign: "middle" }
    })),
    [
      { text: "1", options: { fontSize: 9, color: TEXT, fill: { color: WHITE }, align: "center", bold: true } },
      { text: "Notice of claim or potential claim to any carrier", options: { fontSize: 9, color: TEXT, fill: { color: WHITE } } },
      { text: "✓", options: { fontSize: 13, color: GREEN, fill: { color: "DCFCE7" }, align: "center", bold: true } },
      { text: "✓", options: { fontSize: 13, color: GREEN, fill: { color: "DCFCE7" }, align: "center", bold: true } },
      { text: "✓", options: { fontSize: 13, color: GREEN, fill: { color: "DCFCE7" }, align: "center", bold: true } },
      { text: "Yes *", options: { fontSize: 9, color: AMBER, fill: { color: "FEF9C3" }, align: "center", bold: true } },
      { text: "Free-text description", options: { fontSize: 8, color: MUTED, fill: { color: WHITE }, italics: true } },
    ]
  ];

  s.addTable(riskData, {
    x: 0.45, y: 3.12, w: 9.10, colW: riskColW,
    border: { pt: 0.5, color: "E2E8F0" }, rowH: 0.52,
  });

  // Risk callout
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.45, y: 3.88, w: 9.10, h: 0.52,
    fill: { color: "FEE2E2" }, line: { color: RED, pt: 1 }
  });
  s.addText("★  This single risk assessment question is the lowest-scoring section (16.7%). Different forms ask about 18 months, 3 years, or present it as a claim history table — all mapping to the same BMP field.", {
    x: 0.60, y: 3.88, w: 8.80, h: 0.52,
    fontSize: 9, color: RED, fontFace: "Calibri", italics: true, valign: "middle", margin: 0
  });
}

// ── SLIDE 6 — Employee Category + EPLI Questions ─────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: GRAY };
  sectionHeader(s, "Sections 4 & 5 — Employee Category and EPLI Questions");

  // ── Employee Category ──
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.45, y: 0.90, w: 9.10, h: 0.44,
    fill: { color: AMBER }, line: { color: AMBER }
  });
  s.addText("Section 4 — Employee Category  (13 fields)", {
    x: 0.60, y: 0.90, w: 9.00, h: 0.44,
    fontSize: 13, bold: true, color: WHITE, fontFace: "Georgia", valign: "middle", margin: 0
  });

  const empHeaders = ["Employee Category", "Current Year\nTotal", "Current Year\nCA", "Prior Year\nTotal", "Prior Year\nCA"];
  const empColW    = [3.00, 1.52, 1.52, 1.52, 1.52];
  const empRows = [
    ["Full-time Employees", "# count", "# count", "# count", "# count"],
    ["Part-time Employees", "# count", "# count", "# count", "# count"],
    ["Independent Contractors", "# count", "—", "# count", "—"],
    ["Volunteers", "# count", "—", "—", "—"],
    ["Top 3 States by Employee Count  (State 1 / 2 / 3)", "State + headcount", "—", "—", "—"],
    ["Salary ≥ $125,000  (% of employees)", "% value", "—", "—", "—"],
    ["Salary < $125,000  (% of employees)", "% value", "—", "—", "—"],
  ];

  const empHeaderRow = empHeaders.map(h => ({
    text: h,
    options: { bold: true, color: WHITE, fill: { color: AMBER }, fontSize: 9, align: "center", valign: "middle" }
  }));
  const empDataRows = empRows.map((r, ri) => r.map((cell, ci) => ({
    text: cell,
    options: {
      fontSize: 9,
      color: ci === 0 ? TEXT : MUTED,
      fill: { color: ri % 2 === 0 ? WHITE : "FFFBEB" },
      align: ci === 0 ? "left" : "center",
      bold: ci === 0,
      italics: ci > 0,
    }
  })));

  s.addTable([empHeaderRow, ...empDataRows], {
    x: 0.45, y: 1.40, w: 9.10, colW: empColW,
    border: { pt: 0.5, color: "E2E8F0" }, rowH: 0.38,
  });

  // ── EPLI Specific Questions ──
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.45, y: 4.14, w: 9.10, h: 0.44,
    fill: { color: RED }, line: { color: RED }
  });
  s.addText("Section 5 — EPLI Specific Questions  (10 questions, each Yes / No)", {
    x: 0.60, y: 4.14, w: 9.00, h: 0.44,
    fontSize: 13, bold: true, color: WHITE, fontFace: "Georgia", valign: "middle", margin: 0
  });

  // Two-column list of questions
  const questions = [
    "Q1  Will >50 employees or 5%+ workforce be impacted (terminations)?",
    "Q2  Consulted outside counsel re: workforce reduction?",
    "Q3  Reviewed exempt/nonexempt classifications in last 12 months?",
    "Q4  Completed wage & hour compliance audit in last 12 months?",
    "Q5  Employment dispute / litigation >$10K payment in last 12 months?",
    "Q6  EEOC or similar proceeding in past 3 years?",
    "Q7  Crisis Expense coverage requested?",
    "Q8  Workplace Violence Expense coverage requested?",
    "Q9  Wage and Hour Defense Expenses coverage requested?",
    "Q10 Additional Defense Expense Limit coverage requested?",
  ];

  const half = Math.ceil(questions.length / 2);
  [questions.slice(0, half), questions.slice(half)].forEach((col, ci) => {
    const cx = 0.45 + ci * 4.65;
    col.forEach((q, qi) => {
      const qy = 4.68 + qi * 0.24;
      s.addShape(pres.shapes.RECTANGLE, {
        x: cx, y: qy, w: 4.40, h: 0.22,
        fill: { color: qi % 2 === 0 ? WHITE : "FFF1F1" }, line: { color: "E2E8F0", pt: 0.5 }
      });
      s.addText(q, {
        x: cx + 0.08, y: qy + 0.01, w: 4.24, h: 0.20,
        fontSize: 8.5, color: TEXT, fontFace: "Calibri", valign: "middle", margin: 0
      });
    });
  });
}

// ── SLIDE 7 — Challenges We Faced (with accuracy metrics) ───────────────────
{
  const s = pres.addSlide();
  s.background = { color: GRAY };
  sectionHeader(s, "Challenges We Faced");

  // Each challenge now carries up to 2 metric chips pulled from accuracy_report.txt
  const challenges = [
    {
      num: "1", color: NAVY,
      title: "Diverse Form Layouts",
      body: "Chubb and Travelers use completely different field names, ordering, and page structures — no single extraction template fits all.",
      metrics: [
        { label: "Nature of Operations", val: "55.0%", vc: AMBER },
        { label: "Address – State",      val: "90.0%", vc: GREEN },
      ],
    },
    {
      num: "2", color: RED,
      title: "Inconsistent Question Framing",
      body: "The same data point is asked in different ways: '18 months', 'past 3 years', or embedded in a multi-part table.",
      metrics: [
        { label: "Risk Assessment section", val: "16.7%", vc: RED   },
        { label: "EPLI Q1–Q6 avg",          val: "~30%",  vc: AMBER },
      ],
    },
    {
      num: "3", color: AMBER,
      title: "Checkboxes & Claim Tables",
      body: "Binary answers appear as checkboxes or multi-row claim history tables — formats that LLMs struggle to parse reliably.",
      metrics: [
        { label: "Notice of Claim (13/18 missing)", val: "16.7%", vc: RED },
        { label: "EPL – Duty to Defend",            val: "0.0%",  vc: RED },
      ],
    },
    {
      num: "4", color: BLUE,
      title: "Multi-Part Fields",
      body: "Employee counts split into FT/PT, salary into brackets, states with headcounts — the portal wants structured detail the forms don't always separate.",
      metrics: [
        { label: "Total Employees (8 mismatches)", val: "31.2%", vc: RED   },
        { label: "Top State 1",                    val: "14.3%", vc: RED   },
      ],
    },
    {
      num: "5", color: "1D5EA8",
      title: "Absent or Unlabeled Fields",
      body: "Several fields are not labeled consistently or are missing entirely from some form versions.",
      metrics: [
        { label: "Org Structure (17/17 missing)", val: "0.0%",  vc: RED   },
        { label: "Date of Formation (12/17 miss)",val: "29.4%", vc: RED   },
      ],
    },
    {
      num: "6", color: "7C3AED",
      title: "Semantic Mismatch with BMP Portal",
      body: "The BMP portal's field definitions don't map 1:1 to application fields — different timeframes, granularity, and expected formats.",
      metrics: [
        { label: "Salary Bands (format lost)", val: "0.0%",  vc: RED   },
        { label: "Overall accuracy",           val: "59.4%", vc: AMBER },
      ],
    },
  ];

  // Cards: 2 cols × 3 rows, slightly taller to fit metric chips
  const cw = 4.50, ch = 1.55, rowStep = 1.60;
  challenges.forEach((c, i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = 0.45 + col * 4.85;
    const y = 0.88 + row * rowStep;

    // Card background
    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w: cw, h: ch,
      fill: { color: WHITE }, shadow: makeShadow(), line: { color: "E2E8F0", pt: 1 }
    });

    // Number circle
    s.addShape(pres.shapes.OVAL, {
      x: x + 0.14, y: y + 0.16, w: 0.48, h: 0.48,
      fill: { color: c.color }, line: { color: c.color }
    });
    s.addText(c.num, {
      x: x + 0.14, y: y + 0.16, w: 0.48, h: 0.48,
      fontSize: 13, bold: true, color: WHITE, align: "center",
      fontFace: "Georgia", valign: "middle", margin: 0
    });

    // Title
    s.addText(c.title, {
      x: x + 0.72, y: y + 0.10, w: 3.66, h: 0.38,
      fontSize: 11.5, bold: true, color: TEXT, fontFace: "Georgia", margin: 0
    });

    // Body
    s.addText(c.body, {
      x: x + 0.72, y: y + 0.50, w: 3.66, h: 0.60,
      fontSize: 9.5, color: MUTED, fontFace: "Calibri", lineSpacingMultiple: 1.2, margin: 0
    });

    // Metric chips row — bottom of card
    const chipW = 1.74, chipH = 0.26, chipGap = 0.06;
    c.metrics.forEach((m, mi) => {
      const cx = x + 0.72 + mi * (chipW + chipGap);
      const cy = y + ch - chipH - 0.08;
      s.addShape(pres.shapes.RECTANGLE, {
        x: cx, y: cy, w: chipW, h: chipH,
        fill: { color: GRAY }, line: { color: "E2E8F0", pt: 1 }
      });
      // Colored score badge inside chip
      s.addShape(pres.shapes.RECTANGLE, {
        x: cx, y: cy, w: 0.52, h: chipH,
        fill: { color: m.vc }, line: { color: m.vc }
      });
      s.addText(m.val, {
        x: cx, y: cy, w: 0.52, h: chipH,
        fontSize: 8.5, bold: true, color: WHITE, align: "center",
        fontFace: "Calibri", valign: "middle", margin: 0
      });
      s.addText(m.label, {
        x: cx + 0.56, y: cy + 0.02, w: chipW - 0.60, h: chipH - 0.04,
        fontSize: 7.5, color: TEXT, fontFace: "Calibri", valign: "middle", margin: 0
      });
    });
  });
}

// ── SLIDE 4 — Form Variation Deep Dive: Notice of Claim ─────────────────────
{
  const s = pres.addSlide();
  s.background = { color: GRAY };
  sectionHeader(s, "Form Variation — Notice of Claim Example");

  // Intro text
  s.addText("BMP Portal asks one question. Real applications ask it three different ways.", {
    x: 0.45, y: 0.85, w: 9.10, h: 0.38,
    fontSize: 13, color: MUTED, fontFace: "Calibri", italics: true, margin: 0
  });

  // BMP Portal "source of truth" box — full width, dark
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.45, y: 1.30, w: 9.10, h: 0.62,
    fill: { color: NAVY }, shadow: makeShadow(), line: { color: NAVY }
  });
  s.addText("BMP Portal Field:", {
    x: 0.65, y: 1.30, w: 1.60, h: 0.62,
    fontSize: 11, bold: true, color: ICE, fontFace: "Calibri", valign: "middle", margin: 0
  });
  s.addText("\"Notice of Claim (Past 18 Months)?\"   →   Expected answer: Yes / No", {
    x: 2.30, y: 1.30, w: 7.00, h: 0.62,
    fontSize: 13, bold: true, color: WHITE, fontFace: "Georgia", valign: "middle", margin: 0
  });

  // Three variant cards
  const variants = [
    {
      label: "Variant A — Simple Yes/No",
      forms: "Some Chubb forms",
      color: GREEN,
      text: "\"Has any claim, demand, or suit been made against the applicant in the last 18 months?\"\n\n☐ Yes   ☐ No",
      challenge: "LLM must read checkbox state and map to Yes/No.",
    },
    {
      label: "Variant B — Different Timeframe",
      forms: "Some Travelers forms",
      color: AMBER,
      text: "\"Has any claim, suit, or demand been made against the insured within the past 3 years?\"\n\n☐ Yes   ☐ No",
      challenge: "Timeframe is 3 years, not 18 months. LLM extracts 'No' but portal window differs.",
    },
    {
      label: "Variant C — Claim History Table",
      forms: "Multi-coverage forms",
      color: RED,
      text: "\"List all claims below:\"\n\n  Date  |  Claimant  |  Description  |  Status  |  Amount\n  ——   |   ————  |   ——————  |  ———  |  ————",
      challenge: "Answer is implicit: a filled table means 'Yes'. Empty table means 'No'. LLM struggles to infer this.",
    },
  ];

  const vw = 2.88;
  variants.forEach((v, i) => {
    const vx = 0.45 + i * (vw + 0.24);
    const vy = 2.10;

    // Header
    s.addShape(pres.shapes.RECTANGLE, {
      x: vx, y: vy, w: vw, h: 0.52,
      fill: { color: v.color }, line: { color: v.color }
    });
    s.addText(v.label, {
      x: vx + 0.10, y: vy + 0.02, w: vw - 0.20, h: 0.28,
      fontSize: 10, bold: true, color: WHITE, fontFace: "Georgia", margin: 0
    });
    s.addText(v.forms, {
      x: vx + 0.10, y: vy + 0.28, w: vw - 0.20, h: 0.22,
      fontSize: 9, color: WHITE, fontFace: "Calibri", margin: 0
    });

    // Form text box
    s.addShape(pres.shapes.RECTANGLE, {
      x: vx, y: vy + 0.52, w: vw, h: 1.72,
      fill: { color: WHITE }, line: { color: "E2E8F0", pt: 1 }
    });
    s.addText(v.text, {
      x: vx + 0.10, y: vy + 0.62, w: vw - 0.20, h: 1.52,
      fontSize: 9, color: TEXT, fontFace: "Calibri",
      lineSpacingMultiple: 1.35, valign: "top", margin: 0
    });

    // Challenge callout
    s.addShape(pres.shapes.RECTANGLE, {
      x: vx, y: vy + 2.24, w: vw, h: 0.88,
      fill: { color: v.color === RED ? "FEE2E2" : v.color === AMBER ? "FEF9C3" : "DCFCE7" },
      line: { color: v.color, pt: 1 }
    });
    s.addText("Challenge: " + v.challenge, {
      x: vx + 0.10, y: vy + 2.30, w: vw - 0.20, h: 0.76,
      fontSize: 9, color: TEXT, fontFace: "Calibri",
      lineSpacingMultiple: 1.25, valign: "top", margin: 0
    });
  });
}

// ── VLM POC Slide A: VLM vs LLM — What Changes ──────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: GRAY };
  sectionHeader(s, "VLM vs LLM — What Changes for Risk Assessment");

  // Hero stat banner
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.45, y: 0.84, w: 9.10, h: 0.38,
    fill: { color: NAVY }, line: { color: NAVY }
  });
  s.addText([
    { text: "LLM result: ", options: { color: ICE, fontSize: 10 } },
    { text: "16.7%", options: { color: RED, fontSize: 13, bold: true } },
    { text: "   accuracy  (3/18 correct, 13 missing)          ", options: { color: ICE, fontSize: 10 } },
    { text: "VLM POC: ", options: { color: ICE, fontSize: 10 } },
    { text: "extracted from all 13 tested  ·  fixed both LLM mismatches", options: { color: "86EFAC", fontSize: 10, bold: true } },
  ], {
    x: 0.55, y: 0.84, w: 8.90, h: 0.38,
    fontFace: "Calibri", valign: "middle", margin: 0
  });

  // Column headers
  const colX = [0.45, 3.22, 6.00];
  const colW = 2.60;
  const colTitles = ["LLM Limitation", "Root Cause", "VLM Advantage"];
  const colColors = [RED, AMBER, GREEN];
  colTitles.forEach((t, i) => {
    s.addShape(pres.shapes.RECTANGLE, {
      x: colX[i], y: 1.32, w: colW, h: 0.34,
      fill: { color: colColors[i] }, line: { color: colColors[i] }
    });
    s.addText(t, {
      x: colX[i] + 0.08, y: 1.32, w: colW - 0.16, h: 0.34,
      fontSize: 11, bold: true, color: WHITE, fontFace: "Georgia",
      valign: "middle", margin: 0
    });
  });

  // Comparison rows — each row = one failure mode → cause → fix
  const rows = [
    {
      llm:  "Returned null for 13 of 18 docs — field marked MISSING",
      root: "LLM text extraction finds no explicit '18-month' label; gives up",
      vlm:  "Scans the whole page image; finds the nearest claim question regardless of label wording",
    },
    {
      llm:  "Checkbox state invisible — 'Yes  No' text extracted with no visual cue",
      root: "Plain-text OCR strips checkbox symbols (☑/☐); LLM cannot tell which is marked",
      vlm:  "Sees the visual difference between a filled and empty checkbox directly from the image",
    },
    {
      llm:  "Mismatch: Chubb_EPL_25-26 got 'No' — golden was 'Yes'",
      root: "LLM read '3 years' question and ignored it (timeframe mismatch with 18-mo field)",
      vlm:  "Correctly mapped the '3 years' form question to the BMP '18 months' field; returned 'Yes'",
    },
    {
      llm:  "Mismatch: 4i_Chubb got 'Yes' — golden was 'No'",
      root: "LLM confused an unrelated Illinois-employee question ('past 5 years') with the claim field",
      vlm:  "Identified the correct claim-related section; returned 'No' with confidence 0.9",
    },
    {
      llm:  "No timeframe captured — BMP asks '18 months' but forms differ",
      root: "LLM prompt hard-coded to find '18 months'; other timeframes silently ignored",
      vlm:  "Extracts the actual timeframe from the form (3 yr / 5 yr) and surfaces it separately",
    },
  ];

  const rowH = 0.62, startY = 1.72;
  rows.forEach((r, ri) => {
    const y = startY + ri * (rowH + 0.06);
    const bg = ri % 2 === 0 ? WHITE : "F8FAFF";

    [r.llm, r.root, r.vlm].forEach((txt, ci) => {
      s.addShape(pres.shapes.RECTANGLE, {
        x: colX[ci], y, w: colW, h: rowH,
        fill: { color: bg }, line: { color: "E2E8F0", pt: 0.5 }
      });
      // Left border color per column
      s.addShape(pres.shapes.RECTANGLE, {
        x: colX[ci], y, w: 0.05, h: rowH,
        fill: { color: colColors[ci] }, line: { color: colColors[ci] }
      });
      s.addText(txt, {
        x: colX[ci] + 0.10, y: y + 0.04, w: colW - 0.14, h: rowH - 0.08,
        fontSize: 9, color: TEXT, fontFace: "Calibri",
        lineSpacingMultiple: 1.2, valign: "top", margin: 0
      });
    });
  });

  // Key insight footer
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.45, y: 5.20, w: 9.10, h: 0.28,
    fill: { color: "EEF2FF" }, line: { color: ICE, pt: 1 }
  });
  s.addText(
    "Key insight: Not a single form in our dataset uses an 18-month timeframe. " +
    "Travelers uses 3 years · Chubb D&O/supplemental uses 5 years · Some forms have no claim section at all.",
    {
      x: 0.58, y: 5.20, w: 8.80, h: 0.28,
      fontSize: 8.5, color: NAVY, fontFace: "Calibri", italics: true, valign: "middle", margin: 0
    }
  );
}

// ── VLM POC Slide B: Extraction Results ──────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: GRAY };
  sectionHeader(s, "VLM POC — Notice of Claim Extraction Results  (13 docs)");

  // ── Summary stat cards (top row) ──
  const sumStats = [
    { v: "13",    l: "Docs tested",             c: NAVY  },
    { v: "100%",  l: "Extraction rate\n(0 missing)", c: GREEN },
    { v: "2 / 2", l: "LLM mismatches\ncorrected",   c: GREEN },
    { v: "~0.88", l: "Avg confidence\nscore",        c: BLUE  },
  ];
  sumStats.forEach((st, i) => {
    const sx = 0.45 + i * 2.35;
    s.addShape(pres.shapes.RECTANGLE, {
      x: sx, y: 0.88, w: 2.15, h: 0.96,
      fill: { color: WHITE }, shadow: makeShadow(), line: { color: "E2E8F0", pt: 1 }
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: sx, y: 0.88, w: 2.15, h: 0.06,
      fill: { color: st.c }, line: { color: st.c }
    });
    s.addText(st.v, {
      x: sx + 0.06, y: 0.95, w: 2.03, h: 0.38,
      fontSize: 22, bold: true, color: st.c, align: "center",
      fontFace: "Georgia", margin: 0
    });
    s.addText(st.l, {
      x: sx + 0.06, y: 1.34, w: 2.03, h: 0.42,
      fontSize: 8.5, color: MUTED, align: "center", fontFace: "Calibri",
      lineSpacingMultiple: 1.1, margin: 0
    });
  });

  // ── Results table ──
  // Columns: Document | Timeframe in Form | VLM Answer | Confidence | Status
  const tHeaders = ["Document", "Timeframe in Form", "Answer", "Conf.", "vs. Golden"];
  const tColW    = [3.40, 1.68, 0.82, 0.60, 1.52];

  // Status: ✓ FIXED = was LLM mismatch, now correct
  //         ✓ NEW   = was LLM missing, VLM provides value
  //         ? = no golden to compare
  const vlmRows = [
    ["Chubb_EPL_Application_25-26",         "3 years",        "Yes", "0.9",  "✓ FIXED",  GREEN, "LLM had 'No' — golden is 'Yes'" ],
    ["4i_Chubb_Application",                "5 years",        "No",  "0.9",  "✓ FIXED",  GREEN, "LLM had 'Yes' — golden is 'No'" ],
    ["25-26_EPLI_Application_Travelers3",   "3 years",        "Yes", "0.9",  "✓ NEW",    BLUE,  "LLM was MISSING"                ],
    ["Travelers_App",                       "3 years",        "No",  "0.9",  "✓ NEW",    BLUE,  "LLM was MISSING"                ],
    ["EPL_Application_Pacific_Water",       "3 years",        "No",  "0.9",  "✓ NEW",    BLUE,  "LLM was MISSING"                ],
    ["EPLI_Wodden_Nickle_Enterprises",      "3 years",        "No",  "0.9",  "✓ NEW",    BLUE,  "LLM was MISSING"                ],
    ["Bill_Cramer_Chevrolet",               "3 years",        "No",  "0.9",  "✓ NEW",    BLUE,  "LLM was MISSING"                ],
    ["FF_Chubb_EPLI_11.21.25",              "3 years",        "No",  "0.9",  "✓ NEW",    BLUE,  "LLM was MISSING"                ],
    ["Chubb_App",                           "5 years",        "No",  "0.9",  "✓ NEW",    BLUE,  "LLM was MISSING"                ],
    ["25-26_EPL_CRIME_Chubb_Supp",          "5 years",        "No",  "0.9",  "✓ NEW",    BLUE,  "LLM was MISSING"                ],
    ["24-25_Travelers_Mgmt_Renewal",        "not specified",  "No",  "0.8",  "✓ NEW",    BLUE,  "LLM was MISSING (absence-based)"],
    ["EPLI_-_Chubb_10-01-25",              "not specified",  "No",  "0.8",  "✓ NEW",    BLUE,  "LLM was MISSING (absence-based)"],
    ["SiVEC_Biotech_Chubb",                "not specified",  "No",  "0.8",  "? UNVERIF",MUTED, "No golden to compare"           ],
  ];

  const hdrRow = tHeaders.map(h => ({
    text: h,
    options: { bold: true, color: WHITE, fill: { color: NAVY }, fontSize: 9, align: "center", valign: "middle" }
  }));

  const tableData = [hdrRow, ...vlmRows.map((r, ri) => {
    const rowBg = ri % 2 === 0 ? WHITE : "F4F6FA";
    return [
      { text: r[0], options: { fontSize: 7.5, color: TEXT,  fill: { color: rowBg }, align: "left"   } },
      { text: r[1], options: { fontSize: 8,   color: r[1] === "3 years" ? BLUE : r[1] === "5 years" ? AMBER : MUTED, fill: { color: rowBg }, align: "center", bold: true } },
      { text: r[2], options: { fontSize: 9,   color: r[2] === "Yes" ? GREEN : MUTED, fill: { color: rowBg }, align: "center", bold: true } },
      { text: r[3], options: { fontSize: 8,   color: parseFloat(r[3]) >= 0.9 ? GREEN : AMBER, fill: { color: rowBg }, align: "center" } },
      { text: r[4], options: { fontSize: 8,   color: r[5], fill: { color: rowBg }, align: "center", bold: true } },
    ];
  })];

  s.addTable(tableData, {
    x: 0.45, y: 1.92, w: 8.02, colW: tColW,
    border: { pt: 0.5, color: "E2E8F0" }, rowH: 0.27,
  });

  // ── Timeframe distribution chart (right of table) ──
  s.addChart(pres.charts.PIE, [{
    name: "Timeframe in Form",
    labels: ["3 years\n(Travelers)", "5 years\n(Chubb D&O)", "Not specified\n(absent)"],
    values: [7, 3, 3],
  }], {
    x: 8.55, y: 1.88, w: 1.00, h: 2.20,
    chartColors: [BLUE, AMBER, MUTED],
    showPercent: true,
    dataLabelFontSize: 7,
    showLegend: true,
    legendPos: "b",
    legendFontSize: 6,
    showTitle: true,
    title: "Timeframes",
    titleFontSize: 8,
    titleColor: TEXT,
  });

  // ── Bottom callout ──
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.45, y: 5.16, w: 9.10, h: 0.32,
    fill: { color: "FEF9C3" }, line: { color: AMBER, pt: 1 }
  });
  s.addText(
    "⚠  BMP portal expects 'Past 18 Months' — but 0 of 13 tested forms use an 18-month window. " +
    "7 use 3 years (Travelers), 3 use 5 years (Chubb), 3 have no claim section at all. " +
    "VLM surfaces this mismatch; LLM silently fails.",
    {
      x: 0.58, y: 5.16, w: 8.80, h: 0.32,
      fontSize: 8, color: TEXT, fontFace: "Calibri", italics: true, valign: "middle", margin: 0
    }
  );
}

// ── SLIDE 5 — What LLM Solved vs. Did Not ───────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: GRAY };
  sectionHeader(s, "What the LLM Solved — and What It Didn't");

  // Left column header — Solved
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.45, y: 0.92, w: 4.38, h: 0.52,
    fill: { color: GREEN }, line: { color: GREEN }
  });
  s.addText("✓  LLM Handled Well", {
    x: 0.55, y: 0.92, w: 4.18, h: 0.52,
    fontSize: 14, bold: true, color: WHITE, fontFace: "Georgia", valign: "middle", margin: 0
  });

  // Right column header — Not Solved
  s.addShape(pres.shapes.RECTANGLE, {
    x: 5.17, y: 0.92, w: 4.38, h: 0.52,
    fill: { color: RED }, line: { color: RED }
  });
  s.addText("✗  LLM Struggled With", {
    x: 5.27, y: 0.92, w: 4.18, h: 0.52,
    fontSize: 14, bold: true, color: WHITE, fontFace: "Georgia", valign: "middle", margin: 0
  });

  const solvedItems = [
    "Standard labeled text fields (name, address, contact info)",
    "Numeric fields with clear labels (NAICS code, ZIP, phone)",
    "Simple yes/no checkboxes when labeled explicitly",
    "Currency and date fields formatted consistently",
    "Single-value fields repeated across all form layouts",
    "Website URLs and email addresses",
  ];
  const notSolvedItems = [
    "Fields with different labels/names across Chubb vs Travelers",
    "Questions with different timeframes (18 mo vs 3 yrs)",
    "Claim history tables → inferring a Yes/No answer",
    "Multi-tier salary brackets (e.g., '>$125K' + '<$60K' bands)",
    "State-by-state employee headcounts alongside state names",
    "Organizational structure from checkbox groups (LLC, Corp…)",
    "Fields present in some forms but entirely absent in others",
  ];

  const itemH = 0.54;
  solvedItems.forEach((item, i) => {
    const ry = 1.55 + i * (itemH + 0.06);
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.45, y: ry, w: 4.38, h: itemH,
      fill: { color: WHITE }, line: { color: "E2E8F0", pt: 1 }
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.45, y: ry, w: 0.06, h: itemH,
      fill: { color: GREEN }, line: { color: GREEN }
    });
    s.addText(item, {
      x: 0.60, y: ry + 0.04, w: 4.14, h: itemH - 0.08,
      fontSize: 10, color: TEXT, fontFace: "Calibri", valign: "middle", margin: 0
    });
  });

  notSolvedItems.forEach((item, i) => {
    const ry = 1.55 + i * (itemH + 0.04);
    s.addShape(pres.shapes.RECTANGLE, {
      x: 5.17, y: ry, w: 4.38, h: itemH,
      fill: { color: WHITE }, line: { color: "E2E8F0", pt: 1 }
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: 5.17, y: ry, w: 0.06, h: itemH,
      fill: { color: RED }, line: { color: RED }
    });
    s.addText(item, {
      x: 5.31, y: ry + 0.04, w: 4.14, h: itemH - 0.08,
      fontSize: 10, color: TEXT, fontFace: "Calibri", valign: "middle", margin: 0
    });
  });
}

// ── SLIDE 6 — Overall Results ────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: GRAY };
  sectionHeader(s, "Overall Results");

  // Big accuracy number — left panel
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.45, y: 0.95, w: 3.00, h: 3.80,
    fill: { color: NAVY }, shadow: makeShadow(), line: { color: NAVY }
  });
  s.addText("59.4%", {
    x: 0.45, y: 1.25, w: 3.00, h: 1.40,
    fontSize: 52, bold: true, color: WHITE, align: "center", fontFace: "Georgia", margin: 0
  });
  s.addText("Overall Accuracy", {
    x: 0.45, y: 2.65, w: 3.00, h: 0.40,
    fontSize: 13, color: ICE, align: "center", fontFace: "Calibri", margin: 0
  });
  s.addText("293 / 493 fields correct", {
    x: 0.45, y: 3.08, w: 3.00, h: 0.35,
    fontSize: 11, color: "A8BFEF", align: "center", fontFace: "Calibri", margin: 0
  });
  // Match rate badge
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.75, y: 3.55, w: 2.40, h: 0.52,
    fill: { color: GREEN }, line: { color: GREEN }
  });
  s.addText("20 / 20 Documents Matched  ✓", {
    x: 0.75, y: 3.55, w: 2.40, h: 0.52,
    fontSize: 10, bold: true, color: WHITE, align: "center", fontFace: "Calibri",
    valign: "middle", margin: 0
  });

  // Bar chart — section accuracy
  s.addChart(pres.charts.BAR, [{
    name: "Accuracy %",
    labels: ["General\nInfo", "Employee\nCategory", "Coverage\nDetails", "EPLI\nQuestions", "Risk\nAssessment"],
    values: [69.5, 60.0, 55.9, 29.9, 16.7]
  }], {
    x: 3.70, y: 0.90, w: 5.90, h: 4.00,
    barDir: "col",
    chartColors: [NAVY, BLUE, "1D5EA8", AMBER, RED],
    chartArea: { fill: { color: WHITE }, roundedCorners: false },
    catAxisLabelColor: TEXT,
    valAxisLabelColor: MUTED,
    valAxisMaxVal: 100,
    valGridLine: { color: "E2E8F0", size: 0.5 },
    catGridLine: { style: "none" },
    showValue: true,
    dataLabelPosition: "outEnd",
    dataLabelColor: TEXT,
    dataLabelFontSize: 11,
    dataLabelFontBold: true,
    showLegend: false,
    showTitle: true,
    title: "Accuracy by Section (%)",
    titleFontSize: 13,
    titleColor: TEXT,
  });
}

// ── Processing Performance ───────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: GRAY };
  sectionHeader(s, "Pipeline Processing Performance");

  // ── Data: [label, seconds] sorted ascending ──
  const docs = [
    ["25-26 EPLI Travelers3",      43],
    ["Majestic Care / Chubb Supp", 51],
    ["4i Chubb Application",       55],
    ["BB-SiVEC Biotech",           68],
    ["Farris Motor Co.",           82],
    ["Bill Cramer Chevrolet",      87],
    ["AA-Next",                   106],
    ["Chubb App",                 125],
    ["cc-Friedman & Feiger",      151],
    ["Travelers Private Co.",     152],
    ["Travelers App",             153],
    ["D-Curry Mgmt Corp",         166],
    ["Crime Application",         175],
    ["Industrial Travelers EPL",  176],
    ["Ted's RV Land",             177],
    ["Travelers EPLI App",        190],
    ["E&O APD Med Home Health",   190],
    ["Industrial Water Svc",      201],
    ["EPL App Fillable",          215],
    ["Travelers Crime App",       222],
    ["Wooden Nickle Enterprises", 235],
    ["Entered See File 1071105",  278],
  ];

  // Color per bar: green <90s, amber 90-180s, red >180s
  const barColors = docs.map(([, v]) =>
    v < 90 ? "16A34A" : v <= 180 ? "D97706" : "DC2626"
  );

  // ── Left: 4 stat cards + sequential note ──
  const stats = [
    { v: "43s",    l: "Fastest\n(25-26 EPLI Travelers3)", c: GREEN },
    { v: "4m 38s", l: "Slowest\n(Entered See File…)",     c: RED   },
    { v: "~2m 35s",l: "Average\nper document",            c: AMBER },
    { v: "~6m 51s",l: "Total batch\n(22 documents)",      c: NAVY  },
  ];
  stats.forEach((st, i) => {
    const sx = 0.45 + (i % 2) * 1.85;
    const sy = 0.90 + Math.floor(i / 2) * 1.35;
    s.addShape(pres.shapes.RECTANGLE, {
      x: sx, y: sy, w: 1.72, h: 1.20,
      fill: { color: WHITE }, shadow: makeShadow(), line: { color: "E2E8F0", pt: 1 }
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: sx, y: sy, w: 1.72, h: 0.06,
      fill: { color: st.c }, line: { color: st.c }
    });
    s.addText(st.v, {
      x: sx + 0.06, y: sy + 0.10, w: 1.60, h: 0.55,
      fontSize: 22, bold: true, color: st.c, align: "center",
      fontFace: "Georgia", margin: 0
    });
    s.addText(st.l, {
      x: sx + 0.06, y: sy + 0.66, w: 1.60, h: 0.48,
      fontSize: 8.5, color: MUTED, align: "center", fontFace: "Calibri",
      lineSpacingMultiple: 1.2, margin: 0
    });
  });

  // Sequential processing callout
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.45, y: 3.65, w: 3.72, h: 1.00,
    fill: { color: "FEF9C3" }, line: { color: AMBER, pt: 1 }
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.45, y: 3.65, w: 0.06, h: 1.00,
    fill: { color: AMBER }, line: { color: AMBER }
  });
  s.addText("⚠  Sequential Processing (Rate Limit)", {
    x: 0.60, y: 3.68, w: 3.48, h: 0.28,
    fontSize: 10, bold: true, color: AMBER, fontFace: "Georgia", margin: 0
  });
  s.addText(
    "Documents are processed one at a time due to Azure AI rate limit errors encountered during parallel processing. " +
    "Parallel execution would reduce total batch time to roughly the slowest single document (~4m 38s).",
    {
      x: 0.60, y: 3.98, w: 3.48, h: 0.62,
      fontSize: 8.5, color: TEXT, fontFace: "Calibri",
      lineSpacingMultiple: 1.25, margin: 0
    }
  );

  // ── Right: horizontal bar chart (all 22 docs, sorted) ──
  s.addChart(pres.charts.BAR, [{
    name: "Processing Time (seconds)",
    labels: docs.map(d => d[0]),
    values: docs.map(d => d[1]),
  }], {
    x: 4.30, y: 0.88, w: 5.22, h: 4.55,
    barDir: "bar",   // horizontal
    barGapWidthPct: 35,
    chartColors: barColors,
    chartArea: { fill: { color: WHITE }, roundedCorners: false },
    catAxisLabelColor: TEXT,
    catAxisLabelFontSize: 7.5,
    valAxisLabelColor: MUTED,
    valAxisLabelFontSize: 8,
    valAxisMaxVal: 300,
    valGridLine: { color: "E2E8F0", size: 0.5 },
    catGridLine: { style: "none" },
    showValue: true,
    dataLabelPosition: "outEnd",
    dataLabelColor: TEXT,
    dataLabelFontSize: 7.5,
    dataLabelFormatCode: '0"s"',
    showLegend: false,
    showTitle: true,
    title: "Processing Time per Document (seconds)",
    titleFontSize: 10,
    titleColor: TEXT,
  });

  // Legend chips below chart
  const legend = [
    { label: "< 90s  (fast)",  color: GREEN },
    { label: "90–180s  (mid)", color: AMBER },
    { label: "> 180s  (slow)", color: RED   },
  ];
  legend.forEach((l, li) => {
    const lx = 4.30 + li * 1.74;
    s.addShape(pres.shapes.RECTANGLE, {
      x: lx, y: 5.36, w: 0.16, h: 0.16,
      fill: { color: l.color }, line: { color: l.color }
    });
    s.addText(l.label, {
      x: lx + 0.20, y: 5.32, w: 1.50, h: 0.22,
      fontSize: 8, color: MUTED, fontFace: "Calibri", margin: 0
    });
  });
}

// ── SLIDE 4 — What's Working Well ───────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: GRAY };
  sectionHeader(s, "What's Working Well");

  const topFields = [
    ["Address Fields (Street, City, Zip)", "100%"],
    ["Contact – Telephone & Email", "100%"],
    ["NAICS Code", "100%"],
    ["Risk Mgmt Contact – Name, Title, Phone", "100%"],
    ["Applicant Name", "95.0%"],
    ["Applicant's Website", "90.9%"],
    ["Address – State", "90.0%"],
    ["FT Employees – Current Year Total", "81.2%"],
    ["PT Employees – Current Year Total", "80.0%"],
    ["EPL – Retention Requested", "100%"],
  ];

  // Two columns
  const col = [
    topFields.slice(0, 5),
    topFields.slice(5)
  ];

  col.forEach((items, ci) => {
    const cx = 0.45 + ci * 4.80;
    items.forEach((item, ri) => {
      const ry = 0.98 + ri * 0.86;
      s.addShape(pres.shapes.RECTANGLE, {
        x: cx, y: ry, w: 4.50, h: 0.72,
        fill: { color: WHITE }, shadow: makeShadow(), line: { color: "E2E8F0", pt: 1 }
      });
      // Green accent bar
      s.addShape(pres.shapes.RECTANGLE, {
        x: cx, y: ry, w: 0.06, h: 0.72,
        fill: { color: GREEN }, line: { color: GREEN }
      });
      // Field name
      s.addText(item[0], {
        x: cx + 0.18, y: ry + 0.05, w: 3.10, h: 0.62,
        fontSize: 12, color: TEXT, fontFace: "Calibri", valign: "middle", margin: 0
      });
      // Score badge
      s.addShape(pres.shapes.RECTANGLE, {
        x: cx + 3.32, y: ry + 0.16, w: 0.88, h: 0.38,
        fill: { color: GREEN }, line: { color: GREEN }
      });
      s.addText(item[1], {
        x: cx + 3.32, y: ry + 0.16, w: 0.88, h: 0.38,
        fontSize: 12, bold: true, color: WHITE, align: "center",
        fontFace: "Calibri", valign: "middle", margin: 0
      });
    });
  });
}

// ── SLIDE 5 — Where It Struggles ────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: GRAY };
  sectionHeader(s, "Where It Struggles");

  const badFields = [
    ["Organizational Structure", "0%", RED, "17/17 docs missing — field not found in forms"],
    ["EPL – Duty to Defend", "0%", RED, "Format mismatch: 'selected' vs 'non-duty (no duty to defend)'"],
    ["Risk Assessment (overall)", "16.7%", RED, "Claims / notice questions mostly missing"],
    ["Notice of Claim (Past 18 Mo)", "16.7%", RED, "13/18 scored docs returned no value"],
    ["EPLI Questions Q1–Q6", "25–40%", AMBER, "Yes/No answers absent in 60–70% of docs"],
    ["Date of Formation", "29.4%", AMBER, "12/17 docs missing — field often not labeled clearly"],
    ["Salary Bands", "0%", RED, "Numeric value extracted but bracket detail lost"],
    ["Top State Breakdown", "0–33%", AMBER, "State name captured but employee count stripped"],
  ];

  badFields.forEach((f, i) => {
    const ry = 0.90 + i * 0.60;
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.45, y: ry, w: 9.10, h: 0.52,
      fill: { color: WHITE }, shadow: makeShadow(), line: { color: "E2E8F0", pt: 1 }
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.45, y: ry, w: 0.06, h: 0.52,
      fill: { color: f[2] }, line: { color: f[2] }
    });
    // Score badge
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.60, y: ry + 0.09, w: 0.68, h: 0.34,
      fill: { color: f[2] }, line: { color: f[2] }
    });
    s.addText(f[1], {
      x: 0.60, y: ry + 0.09, w: 0.68, h: 0.34,
      fontSize: 10, bold: true, color: WHITE, align: "center",
      fontFace: "Calibri", valign: "middle", margin: 0
    });
    s.addText(f[0], {
      x: 1.40, y: ry + 0.04, w: 2.60, h: 0.44,
      fontSize: 11, bold: true, color: TEXT, fontFace: "Calibri",
      valign: "middle", margin: 0
    });
    s.addText(f[3], {
      x: 4.10, y: ry + 0.04, w: 5.30, h: 0.44,
      fontSize: 10, color: MUTED, fontFace: "Calibri",
      valign: "middle", margin: 0
    });
  });
}

// ── SLIDE 6 — Error Analysis ─────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: GRAY };
  sectionHeader(s, "Error Analysis — Root Causes");

  const patterns = [
    {
      title: "Format Mismatch",
      color: RED,
      ex: "Got: '1,000000'  →  Expected: '$1,000,000'"
    },
    {
      title: "Partial Extraction",
      color: AMBER,
      ex: "Got: 'dresher ispartnersllc.com'  →  Expected: 'ispartnersllc.com'"
    },
    {
      title: "Missing Structured Detail",
      color: AMBER,
      ex: "Got: '20'  →  Expected: '20 (3 ft + 17 pt)'"
    },
    {
      title: "Binary Q&A Not Extracted",
      color: RED,
      ex: "Q1–Q6 EPLI questions absent in 60–70% of documents"
    },
    {
      title: "Salary Band Detail Lost",
      color: RED,
      ex: "Got: '97%'  →  Expected: '40% ($50k–$150k); 57% (up to $50k)'"
    },
  ];

  // 2 cols × 3 rows (last row spans)
  const positions = [
    { x: 0.45, y: 0.95 }, { x: 5.15, y: 0.95 },
    { x: 0.45, y: 2.68 }, { x: 5.15, y: 2.68 },
    { x: 0.45, y: 4.15 },
  ];
  const cardW = 4.50, cardH = 1.52;

  patterns.forEach((p, i) => {
    const { x, y } = positions[i];
    const w = i === 4 ? 9.10 : cardW;

    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w, h: cardH,
      fill: { color: WHITE }, shadow: makeShadow(), line: { color: "E2E8F0", pt: 1 }
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w, h: 0.50,
      fill: { color: p.color }, line: { color: p.color }
    });
    s.addText(`${i + 1}. ${p.title}`, {
      x: x + 0.14, y: y + 0.08, w: w - 0.28, h: 0.36,
      fontSize: 12, bold: true, color: WHITE, fontFace: "Georgia", margin: 0
    });
    s.addText(p.ex, {
      x: x + 0.14, y: y + 0.60, w: w - 0.28, h: 0.82,
      fontSize: 11, color: TEXT, fontFace: "Calibri",
      italics: true, valign: "top", margin: 0
    });
  });
}

// ── Post-Processing Fixes ────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: GRAY };
  sectionHeader(s, "Post-Processing Fixes — Closing the Gap");

  s.addText("Each error type has a targeted fix that can be applied after LLM extraction, without retraining.", {
    x: 0.45, y: 0.84, w: 9.10, h: 0.30,
    fontSize: 11, color: MUTED, fontFace: "Calibri", italics: true, margin: 0
  });

  // ── Fix data — mirrors the 5 error analysis cards ──
  const fixes = [
    {
      color: RED,
      num: "1",
      error: "Format Mismatch",
      before: "'1,000000'  /  '2m'  /  '3 %'",
      after:  "'$1,000,000'  /  '$2,000,000'  /  '3%'",
      approach: "Regex normalization layer",
      steps: [
        "Currency: prepend $ if absent; fix comma/period separators",
        "Shorthand: 'm' / 'k' → expand to full dollar amount",
        "Percentages: strip stray spaces around % symbol",
        "Dates: convert any format → MM/DD/YYYY",
      ],
    },
    {
      color: AMBER,
      num: "2",
      error: "Partial Extraction",
      before: "'dresher ispartnersllc.com'",
      after:  "'ispartnersllc.com'",
      approach: "Format-aware validation + trim",
      steps: [
        "Run URL regex on extracted value — keep last matching token",
        "Run email regex — discard prefix text before @-domain pattern",
        "Flag and log cases where trim fires for human review",
      ],
    },
    {
      color: AMBER,
      num: "3",
      error: "Missing Structured Detail",
      before: "TotalEmployees: '20'",
      after:  "'20 (3 ft + 17 pt)'",
      approach: "Separate sub-field extraction + reconstruct",
      steps: [
        "Prompt for FT count and PT count as distinct JSON keys",
        "Post-process: if both present, concatenate → 'N (X ft + Y pt)'",
        "Same pattern for state headcounts → 'CA – 36'",
      ],
    },
    {
      color: RED,
      num: "4",
      error: "Binary Q&A Not Extracted",
      before: "Q1–Q6: null in 60–70% of docs",
      after:  "true / false for every question",
      approach: "Targeted second-pass + checkbox detection",
      steps: [
        "Run dedicated yes/no pass per question using keyword anchors",
        "Detect checkbox state: ☑ / ☐ symbols or checked/unchecked tokens",
        "Default to false when no supporting evidence found in document",
        "Log confidence score so borderline answers can be reviewed",
      ],
    },
    {
      color: RED,
      num: "5",
      error: "Salary Band Detail Lost",
      before: "'97%'  or  '56.0 %'",
      after:  "'40% ($50k–$150k); 57% (up to $50k)'",
      approach: "Bracket-aware structured extraction",
      steps: [
        "Extract each salary tier as a separate object: { pct, range }",
        "Post-process array → join as 'X% (range); Y% (range)'",
        "Validate tier percentages sum to ~100%; flag outliers",
      ],
    },
  ];

  // Layout: 2 col × 2 rows (top), 1 full-width card (bottom)
  const positions = [
    { x: 0.45, y: 1.22, w: 4.50 },
    { x: 5.05, y: 1.22, w: 4.50 },
    { x: 0.45, y: 3.04, w: 4.50 },
    { x: 5.05, y: 3.04, w: 4.50 },
    { x: 0.45, y: 4.86, w: 9.10 },  // full-width bottom card
  ];
  const ROW_H_TALL = 1.66;
  const ROW_H_SHORT = 0.76;  // bottom card is short — only 1 row left
  const HDR = 0.38;

  fixes.forEach((f, i) => {
    const { x, y, w } = positions[i];
    const isBottom = i === 4;
    const h = isBottom ? ROW_H_SHORT : ROW_H_TALL;

    // Card shell
    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w, h, fill: { color: WHITE }, shadow: makeShadow(), line: { color: "E2E8F0", pt: 1 }
    });

    // Colored header
    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w, h: HDR, fill: { color: f.color }, line: { color: f.color }
    });

    // Error number + title in header
    s.addText(`${f.num}.  ${f.error}`, {
      x: x + 0.12, y: y + 0.04, w: isBottom ? w * 0.40 : w - 0.24, h: HDR - 0.08,
      fontSize: 11, bold: true, color: WHITE, fontFace: "Georgia", valign: "middle", margin: 0
    });

    // Approach badge (right side of header)
    s.addShape(pres.shapes.RECTANGLE, {
      x: x + (isBottom ? w * 0.42 : w - 1.88), y: y + 0.07,
      w: isBottom ? w * 0.56 : 1.80, h: HDR - 0.14,
      fill: { color: WHITE, transparency: 20 }, line: { color: WHITE, transparency: 40 }
    });
    s.addText("Fix: " + f.approach, {
      x: x + (isBottom ? w * 0.42 : w - 1.88), y: y + 0.07,
      w: isBottom ? w * 0.56 : 1.80, h: HDR - 0.14,
      fontSize: isBottom ? 9 : 8.5, bold: true, color: WHITE,
      align: "center", fontFace: "Calibri", valign: "middle", margin: 0
    });

    if (!isBottom) {
      // Before → After row
      s.addShape(pres.shapes.RECTANGLE, {
        x, y: y + HDR, w, h: 0.30,
        fill: { color: "FEF9F9" }, line: { color: "E2E8F0", pt: 0.5 }
      });
      s.addText([
        { text: "Before: ", options: { bold: true, color: RED,  fontSize: 8.5 } },
        { text: f.before,   options: { color: TEXT, fontSize: 8.5, italics: true } },
        { text: "    →    After: ", options: { bold: true, color: GREEN, fontSize: 8.5 } },
        { text: f.after,    options: { color: TEXT, fontSize: 8.5, italics: true } },
      ], {
        x: x + 0.12, y: y + HDR + 0.02, w: w - 0.24, h: 0.26,
        fontFace: "Consolas", valign: "middle", margin: 0
      });

      // Step bullets
      f.steps.forEach((step, si) => {
        const sy = y + HDR + 0.34 + si * 0.28;
        s.addShape(pres.shapes.OVAL, {
          x: x + 0.14, y: sy + 0.07, w: 0.10, h: 0.10,
          fill: { color: f.color }, line: { color: f.color }
        });
        s.addText(step, {
          x: x + 0.30, y: sy, w: w - 0.42, h: 0.28,
          fontSize: 9, color: TEXT, fontFace: "Calibri", valign: "middle", margin: 0
        });
      });

    } else {
      // Bottom card — horizontal before→after + steps in one line
      s.addShape(pres.shapes.RECTANGLE, {
        x, y: y + HDR, w, h: h - HDR,
        fill: { color: "FEF9F9" }, line: { color: "E2E8F0", pt: 0.5 }
      });
      s.addText([
        { text: "Before: ", options: { bold: true, color: RED,   fontSize: 9 } },
        { text: f.before,   options: { color: TEXT, fontSize: 9, italics: true } },
        { text: "   →   After: ", options: { bold: true, color: GREEN, fontSize: 9 } },
        { text: f.after,    options: { color: TEXT, fontSize: 9, italics: true } },
        { text: "   |   ", options: { color: MUTED, fontSize: 9 } },
        { text: f.steps[0], options: { color: MUTED, fontSize: 9 } },
      ], {
        x: x + 0.14, y: y + HDR + 0.04, w: w - 0.28, h: h - HDR - 0.08,
        fontFace: "Calibri", valign: "middle", margin: 0
      });
    }
  });
}

// ── SLIDE 7 — Next Steps ─────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: GRAY };
  sectionHeader(s, "Next Steps & Recommendations");

  const recs = [
    {
      num: "01",
      title: "Format Normalization",
      body: "Post-process extracted values to standardize currency ($1,000,000), percentages, and date formats before scoring.",
      color: NAVY,
    },
    {
      num: "02",
      title: "Structured Yes/No Extraction",
      body: "Improve prompt engineering for binary EPLI questions (Q1–Q6) — currently missing in 60–70% of documents.",
      color: BLUE,
    },
    {
      num: "03",
      title: "Employee Breakdown Parsing",
      body: "Extract FT/PT split and state headcounts as sub-fields rather than collapsing to a single number.",
      color: "1D5EA8",
    },
    {
      num: "04",
      title: "Organizational Structure Detection",
      body: "Add dedicated extraction logic for entity type (LLC, Corp, etc.) — currently 0% — using form checkbox parsing.",
      color: AMBER,
    },
    {
      num: "05",
      title: "Salary Band Detail Retention",
      body: "Preserve salary bracket labels (e.g., '>$125K') alongside percentages; current extraction drops the bracket context.",
      color: RED,
    },
    {
      num: "06",
      title: "Expand Golden Set",
      body: "Grow from 20 to 50+ documents to improve statistical confidence and catch edge cases across more form layouts.",
      color: GREEN,
    },
  ];

  const cw = 4.50, ch = 1.42;
  recs.forEach((r, i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = 0.45 + col * 4.85;
    const y = 0.90 + row * 1.52;

    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w: cw, h: ch,
      fill: { color: WHITE }, shadow: makeShadow(), line: { color: "E2E8F0", pt: 1 }
    });
    // Number circle background
    s.addShape(pres.shapes.OVAL, {
      x: x + 0.14, y: y + 0.18, w: 0.50, h: 0.50,
      fill: { color: r.color }, line: { color: r.color }
    });
    s.addText(r.num, {
      x: x + 0.14, y: y + 0.18, w: 0.50, h: 0.50,
      fontSize: 12, bold: true, color: WHITE, align: "center",
      fontFace: "Georgia", valign: "middle", margin: 0
    });
    s.addText(r.title, {
      x: x + 0.74, y: y + 0.12, w: 3.62, h: 0.40,
      fontSize: 12, bold: true, color: TEXT, fontFace: "Georgia", margin: 0
    });
    s.addText(r.body, {
      x: x + 0.74, y: y + 0.54, w: 3.62, h: 0.78,
      fontSize: 10, color: MUTED, fontFace: "Calibri", lineSpacingMultiple: 1.25, margin: 0
    });
  });
}

// ── SLIDE 8 — Appendix: Full Field Accuracy ──────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: GRAY };
  sectionHeader(s, "Appendix — Full Field Accuracy");

  const rows = [
    ["Field", "Score", "%"],
    ["Address (Street / City / Zip)", "60/60", "100%"],
    ["Contact – Telephone & Email", "17/17", "100%"],
    ["NAICS Code", "9/9", "100%"],
    ["Risk Mgmt Contact (Name/Title/Phone)", "3/3", "100%"],
    ["EPL – Retention Requested", "4/4", "100%"],
    ["FT Employees – Prior Year CA", "3/3", "100%"],
    ["Volunteers", "1/1", "100%"],
    ["Applicant Name", "19/20", "95%"],
    ["Applicant's Website", "10/11", "90.9%"],
    ["Address – State", "18/20", "90%"],
    ["EPL – Current Carrier", "4/5", "80%"],
    ["Requested Effective Date", "5/6", "83.3%"],
    ["FT Employees – Current Year Total", "13/16", "81.2%"],
    ["PT Employees – Current Year Total / Prior", "16/20", "80%"],
    ["FT Employees – Prior Year Total", "4/5", "80%"],
    ["EPL – Limit Requested", "6/8", "75%"],
    ["Total Number of Locations", "5/7", "71.4%"],
    ["Nature of Operations", "11/20", "55%"],
    ["Employees – California", "7/14", "50%"],
    ["EPL – Current Retention", "2/4", "50%"],
    ["EPL – Current Limit", "3/5", "60%"],
    ["Independent Contractors", "11/16", "68.8%"],
    ["Contact – Name", "12/14", "85.7%"],
    ["Total Number of Employees", "5/16", "31.2%"],
    ["Employees – U.S.", "1/4", "25%"],
    ["Employees – Outside U.S. & CAN", "4/12", "33.3%"],
    ["EPLI Q1 (terminations)", "4/10", "40%"],
    ["EPLI Q2 (outside counsel)", "3/9", "33.3%"],
    ["EPLI Q3–Q4 (wage/hour)", "4/16", "25%"],
    ["EPLI Q5 (employment dispute)", "5/17", "29.4%"],
    ["EPLI Q6 (EEOC)", "4/15", "26.7%"],
    ["Date of Formation", "5/17", "29.4%"],
    ["Notice of Claim (Past 18 Mo)", "3/18", "16.7%"],
    ["Contact – Title", "3/10", "30%"],
    ["Organizational Structure", "0/17", "0%"],
    ["EPL – Duty to Defend", "0/8", "0%"],
    ["Salary >= $125K (%)", "0/4", "0%"],
    ["Salary < $125K (%)", "0/5", "0%"],
    ["Top State 1 / 2 / 3", "2/12", "17%"],
  ];

  // Color rows by performance
  function rowFill(pct) {
    const v = parseFloat(pct);
    if (isNaN(v) || pct === "%") return { color: NAVY };
    if (v >= 80) return { color: "DCFCE7" };
    if (v >= 50) return { color: "FEF9C3" };
    return { color: "FEE2E2" };
  }
  function rowColor(pct) {
    const v = parseFloat(pct);
    if (isNaN(v) || pct === "%") return WHITE;
    if (v >= 80) return GREEN;
    if (v >= 50) return AMBER;
    return RED;
  }

  const tableData = rows.map((row, ri) => {
    if (ri === 0) {
      return row.map(cell => ({
        text: cell,
        options: { bold: true, color: WHITE, fill: { color: NAVY }, fontSize: 10, align: "center" }
      }));
    }
    const fill = rowFill(row[2]);
    return [
      { text: row[0], options: { fontSize: 9, color: TEXT, fill, align: "left" } },
      { text: row[1], options: { fontSize: 9, color: TEXT, fill, align: "center" } },
      { text: row[2], options: { fontSize: 9, bold: true, color: rowColor(row[2]), fill, align: "center" } },
    ];
  });

  s.addTable(tableData, {
    x: 0.45, y: 0.88, w: 9.10,
    colW: [5.80, 1.50, 1.80],
    border: { pt: 0.5, color: "E2E8F0" },
    autoPage: false,
    fontSize: 9,
  });
}

// ── Write file ────────────────────────────────────────────────────────────────
pres.writeFile({ fileName: "/Users/thameem/Desktop/Spring-2026/BMP2/semantic-extraction/reports/Semantic_Extraction_Results.pptx" })
  .then(() => console.log("✅  Saved: reports/Semantic_Extraction_Results.pptx"))
  .catch(err => { console.error("❌  Error:", err); process.exit(1); });
