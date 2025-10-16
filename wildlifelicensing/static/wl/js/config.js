require.config({
  baseUrl: "/static/wl",
  paths: {
    jQuery: "//static.dpaw.wa.gov.au/static/libs/jquery/2.2.0/jquery.min",
    // Use the Bootstrap 5 bundle (includes Popper) so JS matches the BS5 markup/CSS
    bootstrap:
      "https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min",
    "bootstrap-datetimepicker":
      "//static.dpaw.wa.gov.au/static/libs/bootstrap-datetimepicker/4.17.37/js/bootstrap-datetimepicker.min",
    // Use Select2 v4 full bundle (includes compat modules) to work with RequireJS
    select2:
      "https://cdn.jsdelivr.net/npm/select2@4.0.13/dist/js/select2.full.min",
    handlebars:
      "//static.dpaw.wa.gov.au/static/libs/handlebars.js/4.0.5/handlebars.amd.min",
    "handlebars.runtime":
      "//static.dpaw.wa.gov.au/static/libs/handlebars.js/4.0.5/handlebars.runtime.amd.min",
    moment: "//static.dpaw.wa.gov.au/static/libs/moment.js/2.9.0/moment.min",
    parsley: "//static.dpaw.wa.gov.au/static/libs/parsley.js/2.3.5/parsley.min",
    "datatables.net":
      "https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min",
    // DataTables Bootstrap 5 integration
    "datatables.bootstrap":
      "https://cdn.datatables.net/1.13.6/js/dataTables.bootstrap5.min",
    lodash: "//static.dpaw.wa.gov.au/static/libs/lodash.js/4.5.1/lodash.min",
    "bootstrap.treeView":
      "//static.dpaw.wa.gov.au/static/libs/bootstrap-treeview/1.2.0/bootstrap-treeview.min",
    "datatables.datetime":
      "//cdn.datatables.net/plug-ins/1.10.11/sorting/datetime-moment",
  },
  map: {
    "*": {
      jquery: "jQuery",
      datatables: "datatables.net",
    },
  },
  shim: {
    jQuery: {
      exports: "$",
    },
    lodash: {
      exports: "_",
    },
    bootstrap: {
      deps: ["jQuery"],
      exports: "bootstrap",
    },
    "bootstrap-datetimepicker": {
      deps: ["jQuery", "bootstrap", "moment"],
    },
    select2: {
      // Select2 v4 is AMD-aware; only depend on jQuery here.
      deps: ["jQuery"],
    },
    parsley: {
      deps: ["jQuery"],
    },
    "datatables.net": {
      deps: ["jQuery"],
    },
    "datatables.bootstrap": {
      deps: ["jQuery"],
    },
    "bootstrap.treeView": {
      deps: ["bootstrap"],
    },
  },
});
