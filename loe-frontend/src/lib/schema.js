// src/lib/schema.js

// Minimal, safe defaults the editors/generator expect.
export const DEFAULT_SCHEMA = {
  loe_type: "rack_stack",

  // Project
  client: "",
  project_name: "",
  service: "Rack & Stack",
  scope: "",
  environment: "",
  timeline: "",

  // Multi-site – per-site is the source of truth
  sites: [
    {
      site_id: "",
      name: "",
      address: "",
      country: "",
      assumptions: [],
      constraints: [],
      out_of_scope: [],
      bom: [],
      optics_bom: [],
      tasks: {
        site_survey:        { include: null, engineers: null, days: null, steps: [] },
        installation:       { include: true,  engineers: null, days: null, steps: [] },
        optics_installation:{ include: null, engineers: null, days: null, steps: [] },
        post_install:       { include: null, engineers: null, days: null, steps: [] },
      },
    },
  ],

  // Top-level BOM is intentionally unused now
  bom: [],

  // Global toggles
  global_scope: {
    rack_and_stack:      { include: true,  notes: "" },
    site_survey:         { include: null, notes: "" },
    optics_installation: { include: null, notes: "" },
    post_install:        { include: null, notes: "" },
  },

  // Misc
  notes_raw: "",

  staging: {
    ic_used: false,
    doa: false,
    burn_in: false,
    labelling: "",
    packing: "",
  },

  rollout: {
    waves: "",
    floors: "",
    ooh_windows: "",
    change_approvals: "",
  },

  visits_caps: {
    install_max_visits: null,
    post_deploy_max_visits: null,
    site_survey_window_weeks: null,
  },

  brackets: [],

  counts: {
    devices_total: null,
    aps_ordered: null,
    aps_to_mount: null,
  },

  governance: {
    pm: "",
    comms_channels: "",
    escalation: "",
  },

  handover: {
    docs: "",
    acceptance_criteria: "",
  },

  wave_plan: [],
  prerequisites: [],
  assumptions: [],
  out_of_scope: [],
  constraints: [],
  deliverables: [],
};

export const makeDefaultSchema = (loe_type = "rack_stack") => ({
  ...DEFAULT_SCHEMA,
  loe_type,
});
