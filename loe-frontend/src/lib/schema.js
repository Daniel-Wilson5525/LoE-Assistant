// src/lib/schema.js

// Minimal, safe defaults the editors/generator expect.
// Keep fields but leave values empty so the model never hallucinates.
export const DEFAULT_SCHEMA = {
  loe_type: "rack_stack",
  client: "",
  project_name: "",
  service: "rack and stack",
  scope: "",
  environment: "",
  timeline: "",
  sites: [{ name: "", address: "" }],
  devices: [],                     // optional lightweight device list
  bom: [],                         // detailed Bill of Materials rows
  deliverables: [],
  constraints: [],
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
    pm_client: "",
    pm_wwt: "",
    comms_channel: "",
    change_approvals: "",
    escalation: "",
  },
  handover: {
    deliverables: [],
    acceptance_criteria: "",
    docs: "",
  },
  wave_plan: [],
  prerequisites: [],
  assumptions: [],
  out_of_scope: [],
};

// Helper if you want to set the type on the fly
export const makeDefaultSchema = (loe_type = "rack_stack") => ({
  ...DEFAULT_SCHEMA,
  loe_type,
});
