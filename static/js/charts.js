(function () {
  function isDarkTheme() {
    return document.documentElement.getAttribute('data-bs-theme') === 'dark';
  }

  function axisLabelStyle() {
    return { colors: isDarkTheme() ? '#9ca3af' : '#6b7280', fontSize: '12px' };
  }

  function gridOptions() {
    return {
      borderColor: isDarkTheme() ? '#374151' : '#f3f4f6',
      strokeDashArray: 4,
    };
  }

  function areaOptions(config) {
    return {
      chart: {
        type: 'area',
        height: config.height || 350,
        fontFamily: "'Segoe UI', system-ui, -apple-system, sans-serif",
        toolbar: { show: false }
      },
      series: [{ name: config.seriesName, data: config.seriesData }],
      xaxis: {
        categories: config.labels,
        tickAmount: Math.min(config.labels.length, 12),
        labels: {
          style: axisLabelStyle(),
          rotate: -45,
          trim: true
        },
        axisBorder: { show: false },
        axisTicks: { show: false }
      },
      yaxis: {
        labels: {
          style: axisLabelStyle(),
          formatter: config.yLabelFormatter
        }
      },
      dataLabels: { enabled: false },
      stroke: { curve: 'smooth', width: config.strokeWidth || 2, colors: [config.color] },
      fill: {
        type: 'gradient',
        gradient: {
          shadeIntensity: 1,
          opacityFrom: 0.25,
          opacityTo: 0.05,
          stops: [0, 90, 100],
          colorStops: [
            { offset: 0, color: config.color, opacity: 0.25 },
            { offset: 100, color: config.color, opacity: 0.05 }
          ]
        }
      },
      grid: Object.assign(gridOptions(), config.gridExtras || {}),
      tooltip: {
        theme: isDarkTheme() ? 'dark' : 'light',
        x: { formatter: config.tooltipXFormatter || function (val) { return val; } },
        y: { formatter: config.tooltipYFormatter }
      },
      markers: {
        size: 0,
        colors: [isDarkTheme() ? '#1f2937' : '#fff'],
        strokeColors: config.color,
        strokeWidth: 2,
        hover: { size: 5 }
      }
    };
  }

  window.BookWiseCharts = {
    areaOptions: areaOptions,
    axisLabelStyle: axisLabelStyle,
    gridOptions: gridOptions,
    isDarkTheme: isDarkTheme,
  };
})();

