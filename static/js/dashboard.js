(() => {
  const d = window.dashboardData || {};
  const s = window.statusData || { approved: 0, rejected: 0 };

  // Make sure all labels are valid strings
  const safeLabels = (value) => {
    if (!Array.isArray(value)) return [];

    return value.map((item) => {
      if (item === null || item === undefined || item === "") {
        return "Not specified";
      }

      return String(item);
    });
  };

  // Make sure all chart values are valid numbers
  const safeValues = (value) => {
    if (!Array.isArray(value)) return [];

    return value.map((item) => {
      const number = Number(item);

      return Number.isFinite(number) ? number : 0;
    });
  };

  const commonOptions = {
    responsive: true,
    maintainAspectRatio: false,

    interaction: {
      mode: "index",
      intersect: false
    },

    plugins: {
      legend: {
        position: "bottom"
      },

      tooltip: {
        enabled: true
      }
    }
  };

  // Safely create chart
  const makeChart = (id, config) => {
    const canvas = document.getElementById(id);

    if (!canvas) {
      console.warn(`Chart canvas not found: ${id}`);
      return;
    }

    if (!window.Chart) {
      console.error("Chart.js is not loaded");
      return;
    }

    // Prevent duplicate chart error
    const existingChart = Chart.getChart(canvas);

    if (existingChart) {
      existingChart.destroy();
    }

    new Chart(canvas, config);
  };

  /*
  ==========================================================
  COMMON OPTIONS FOR THE 4 CATEGORY CHARTS
  ==========================================================
  */

  const categoryBarOptions = {
    responsive: true,
    maintainAspectRatio: false,

    indexAxis: "y",

    interaction: {
      mode: "nearest",
      intersect: false
    },

    plugins: {
      legend: {
        display: false
      },

      tooltip: {
        enabled: true
      }
    },

    scales: {
      x: {
        beginAtZero: true,

        ticks: {
          precision: 0
        },

        title: {
          display: true,
          text: "Number of Quotations"
        }
      },

      y: {
        beginAtZero: true
      }
    }
  };

  /*
  ==========================================================
  ADVISOR PERFORMANCE
  ==========================================================
  */

  makeChart("advisorChart", {
    type: "bar",

    data: {
      labels: safeLabels(d.advisor_labels),

      datasets: [
        {
          label: "Total",
          data: safeValues(d.advisor_totals)
        },

        {
          label: "Approved",
          data: safeValues(d.advisor_approved)
        }
      ]
    },

    options: commonOptions
  });

  /*
  ==========================================================
  APPROVAL RATE BY ADVISOR
  ==========================================================
  */

  makeChart("advisorRateChart", {
    type: "bar",

    data: {
      labels: safeLabels(d.advisor_labels),

      datasets: [
        {
          label: "Approval %",
          data: safeValues(d.advisor_rates)
        }
      ]
    },

    options: {
      ...commonOptions,

      scales: {
        y: {
          beginAtZero: true,
          max: 100,

          ticks: {
            callback: function (value) {
              return value + "%";
            }
          }
        }
      }
    }
  });

  /*
  ==========================================================
  QUOTED VALUE BY ADVISOR
  ==========================================================
  */

  makeChart("advisorValueChart", {
    type: "bar",

    data: {
      labels: safeLabels(d.advisor_labels),

      datasets: [
        {
          label: "Quoted BHD",
          data: safeValues(d.advisor_quoted_values)
        },

        {
          label: "Approved BHD",
          data: safeValues(d.advisor_approved_values)
        }
      ]
    },

    options: commonOptions
  });

  /*
  ==========================================================
  STATUS DISTRIBUTION
  ==========================================================
  */

  makeChart("statusChart", {
    type: "doughnut",

    data: {
      labels: [
        "Approved",
        "Rejected"
      ],

      datasets: [
        {
          data: [
            Number(s.approved) || 0,
            Number(s.rejected) || 0
          ]
        }
      ]
    },

    options: commonOptions
  });

  /*
  ==========================================================
  VEHICLE TYPES
  ==========================================================
  */

  makeChart("vehicleChart", {
    type: "bar",

    data: {
      labels: safeLabels(d.vehicle_labels),

      datasets: [
        {
          label: "Quotations",
          data: safeValues(d.vehicle_values)
        }
      ]
    },

    options: categoryBarOptions
  });

  /*
  ==========================================================
  SERVICE OFFERED
  ==========================================================
  */

  makeChart("serviceChart", {
    type: "bar",

    data: {
      labels: safeLabels(d.service_labels),

      datasets: [
        {
          label: "Quotations",
          data: safeValues(d.service_values)
        }
      ]
    },

    options: categoryBarOptions
  });

  /*
  ==========================================================
  DAMAGE AREAS
  ==========================================================
  */

  makeChart("damageChart", {
    type: "bar",

    data: {
      labels: safeLabels(d.damage_labels),

      datasets: [
        {
          label: "Quotations",
          data: safeValues(d.damage_values)
        }
      ]
    },

    options: categoryBarOptions
  });

  /*
  ==========================================================
  REASONS FOR REFUSAL
  ==========================================================
  */

  makeChart("refusalChart", {
    type: "bar",

    data: {
      labels: safeLabels(d.refusal_labels),

      datasets: [
        {
          label: "Rejected Quotations",
          data: safeValues(d.refusal_values)
        }
      ]
    },

    options: categoryBarOptions
  });

  /*
  ==========================================================
  DAILY TIME SERIES
  ==========================================================
  */

  makeChart("timeSeriesChart", {
    type: "line",

    data: {
      labels: safeLabels(d.daily_labels),

      datasets: [
        {
          label: "Total",
          data: safeValues(d.daily_totals),
          tension: 0.2,
          fill: false
        },

        {
          label: "Approved",
          data: safeValues(d.daily_approved),
          tension: 0.2,
          fill: false
        },

        {
          label: "Rejected",
          data: safeValues(d.daily_rejected),
          tension: 0.2,
          fill: false
        }
      ]
    },

    options: {
      ...commonOptions,

      scales: {
        y: {
          beginAtZero: true,

          ticks: {
            precision: 0
          }
        }
      }
    }
  });

  /*
  ==========================================================
  MONTHLY TREND
  ==========================================================
  */

  makeChart("trendChart", {
    type: "line",

    data: {
      labels: safeLabels(d.month_labels),

      datasets: [
        {
          label: "Quotations",
          data: safeValues(d.month_values),
          tension: 0.25,
          fill: false
        }
      ]
    },

    options: commonOptions
  });

  /*
  ==========================================================
  QUOTATIONS BY HOUR
  ==========================================================
  */

  makeChart("hourChart", {
    type: "line",

    data: {
      labels: safeLabels(d.hour_labels),

      datasets: [
        {
          label: "Quotations",
          data: safeValues(d.hour_values),
          tension: 0.25
        }
      ]
    },

    options: commonOptions
  });

  /*
  ==========================================================
  QUOTATIONS BY WEEKDAY
  ==========================================================
  */

  makeChart("weekdayChart", {
    type: "bar",

    data: {
      labels: safeLabels(d.weekday_labels),

      datasets: [
        {
          label: "Quotations",
          data: safeValues(d.weekday_values)
        }
      ]
    },

    options: commonOptions
  });
})();


/*
==========================================================
AUTO REFRESH
==========================================================
*/

setInterval(() => {
  if (
    document.visibilityState === "visible" &&
    !document.querySelector("input:focus, select:focus")
  ) {
    window.location.reload();
  }
}, 60000);