/* ================================
   MEMBERS & FAMILY MANAGEMENT JAVASCRIPT
   ================================ */

// Member Management Functions
function showAddMemberModal() {
  document.getElementById("addMemberModal").style.display = "block";
}

function editMember(memberId, name, relationship) {
  document.getElementById("editMemberId").value = memberId;
  document.getElementById("editMemberName").value = name;
  document.getElementById("editMemberRelationship").value = relationship;
  document.getElementById("editMemberModal").style.display = "block";
}

function deleteMember(memberId, name) {
  if (confirm(`Are you sure you want to remove ${name} from the family?`)) {
    fetch(`/delete_member/${memberId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    })
      .then((response) => {
        if (response.ok) {
          location.reload();
        } else {
          alert("Error deleting member");
        }
      })
      .catch((error) => {
        console.error("Error deleting member:", error);
        alert("Error deleting member");
      });
  }
}

// Member Dropdown Functionality (integrated as toggle-select)
function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.style.display = "none";
  }
}

// Chart Management Functions

let chartInstance;
let pieChartInstance;

// Normalize various backend data shapes into { labels:[], values:[], colors:[] }
function toChartDataset(raw) {
  if (!raw) return { labels: [], values: [], colors: [] };

  // Already in desired shape
  if (Array.isArray(raw.labels) && Array.isArray(raw.values)) {
    return {
      labels: raw.labels,
      values: raw.values,
      colors: raw.colors || generateColors(raw.labels.length),
    };
  }

  // Array of objects like [{category, amount}]
  if (Array.isArray(raw)) {
    const labels = raw.map((x) => x.category ?? x.label ?? x.name ?? "");
    const values = raw.map((x) => Number(x.amount ?? x.value ?? 0));
    return { labels, values, colors: generateColors(labels.length) };
  }

  // Object map {category: amount}
  if (typeof raw === "object") {
    const labels = Object.keys(raw);
    const values = labels.map((k) => Number(raw[k] ?? 0));
    return { labels, values, colors: generateColors(labels.length) };
  }

  return { labels: [], values: [], colors: [] };
}

function createChart(canvasId, data, chartTitle) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return null;

  // Destroy existing chart if it exists
  if (chartInstance) {
    chartInstance.destroy();
    chartInstance = null;
  }

  // Normalize incoming data shape
  const normalized = toChartDataset(data);
  const hasData =
    Array.isArray(normalized.labels) && normalized.labels.length > 0;
  if (!hasData) {
    // Render a friendly placeholder message
    const ctx2d = canvas.getContext("2d");
    ctx2d.clearRect(0, 0, canvas.width, canvas.height);
    ctx2d.font = "14px Arial";
    ctx2d.fillStyle = "#666";
    ctx2d.textAlign = "center";
    const msg =
      chartTitle && chartTitle.includes("Family")
        ? "No family category data available"
        : "No category data available";
    ctx2d.fillText(msg, canvas.width / 2, canvas.height / 2);
    return null;
  }

  const colors = [
    "#4A90E2",
    "#50C878",
    "#FF6B6B",
    "#FFA500",
    "#9B59B6",
    "#1ABC9C",
    "#E74C3C",
    "#3498DB",
  ];

  // Create a simple bar chart showing current category totals
  const datasets = [
    {
      label: "Spending by Category",
      data: normalized.values,
      backgroundColor:
        normalized.colors || colors.slice(0, normalized.labels.length),
      borderWidth: 1,
      borderColor: "#fff",
    },
  ];

  const chartConfig = {
    type: "bar",
    data: {
      labels: normalized.labels,
      datasets: datasets,
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        title: {
          display: true,
          text: chartTitle || "Category Spending",
          font: { size: 16, weight: "bold" },
        },
        legend: {
          display: false,
        },
        tooltip: {
          callbacks: {
            label: function (context) {
              const value = context.parsed.y;
              return `£${value.toFixed(2)}`;
            },
          },
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            callback: function (value) {
              return "£" + value.toFixed(0);
            },
          },
          grid: {
            color: "#e9ecef",
          },
        },
        x: {
          grid: {
            display: false,
          },
        },
      },
    },
  };

  chartInstance = new Chart(canvas, chartConfig);
  return chartInstance;
}

function generateColors(count) {
  const colors = [
    "#FF6384",
    "#36A2EB",
    "#FFCE56",
    "#4BC0C0",
    "#9966FF",
    "#FF9F40",
    "#FF6384",
    "#C9CBCF",
    "#4BC0C0",
    "#FF6384",
  ];
  const result = [];
  for (let i = 0; i < count; i++) {
    result.push(colors[i % colors.length]);
  }
  return result;
}

function updatePieChart(data) {
  const canvas = document.getElementById("familyMonthlyComparisonChart");
  if (!canvas) return;

  const pieData = toChartDataset(data);

  if (pieData.labels.length === 0) {
    // No data - destroy chart and show message
    if (pieChartInstance) {
      pieChartInstance.destroy();
      pieChartInstance = null;
    }
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.font = "14px Arial";
    ctx.fillStyle = "#666";
    ctx.textAlign = "center";
    ctx.fillText(
      "No expense data available",
      canvas.width / 2,
      canvas.height / 2
    );
    return;
  }

  const pieColors = [
    "#FF6B6B",
    "#4ECDC4",
    "#FFE66D",
    "#95E1D3",
    "#A8E6CF",
    "#FF8B94",
    "#C7CEEA",
    "#FFDAC1",
  ];

  // If chart exists, update it; otherwise create new
  if (pieChartInstance) {
    pieChartInstance.data.labels = pieData.labels;
    pieChartInstance.data.datasets[0].data = pieData.values;
    pieChartInstance.data.datasets[0].backgroundColor = pieColors.slice(
      0,
      pieData.labels.length
    );
    pieChartInstance.update();
  } else {
    const ctx = canvas.getContext("2d");
    pieChartInstance = new Chart(ctx, {
      type: "pie",
      data: {
        labels: pieData.labels,
        datasets: [
          {
            label: "Expenses by Category",
            data: pieData.values,
            backgroundColor: pieColors.slice(0, pieData.labels.length),
            borderColor: "#fff",
            borderWidth: 2,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: true,
            position: "right",
            labels: {
              padding: 15,
              font: { size: 12 },
              generateLabels: function (chart) {
                const data = chart.data;
                if (data.labels.length && data.datasets.length) {
                  const dataset = data.datasets[0];
                  const total = dataset.data.reduce((a, b) => a + b, 0);
                  return data.labels.map((label, i) => {
                    const value = dataset.data[i];
                    const percentage = ((value / total) * 100).toFixed(1);
                    return {
                      text: `${label} (${percentage}%)`,
                      fillStyle: dataset.backgroundColor[i],
                      hidden: false,
                      index: i,
                    };
                  });
                }
                return [];
              },
            },
          },
          tooltip: {
            callbacks: {
              label: function (context) {
                const label = context.label || "";
                const value = context.parsed;
                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                const percentage = ((value / total) * 100).toFixed(1);
                return `${label}: £${value.toFixed(2)} (${percentage}%)`;
              },
            },
          },
        },
      },
    });
  }
}

function updateChart(view) {
  const memberSelect =
    document.getElementById("perMemberSelect") ||
    document.getElementById("memberSelect");

  if (!familyData || !memberData) {
    console.error("Chart data not available");
    return;
  }

  if (view === "member") {
    const selectedMember = memberSelect && memberSelect.value;
    const raw =
      (selectedMember && memberData && memberData[selectedMember]) || [];
    const data = toChartDataset(raw);
    createChart(
      "categoryChart",
      data,
      `${selectedMember} - Expense Categories`
    );
    // Update pie chart for selected member
    updatePieChart(raw);
  } else {
    createChart(
      "categoryChart",
      toChartDataset(familyData),
      "Family - Expense Categories"
    );
    // Update pie chart for whole family
    updatePieChart(familyData);
  }
}

// Modal Functions (Non-member modals)
function showAddExpenseModal() {
  // Set today's date as default
  const today = new Date().toISOString().split("T")[0];
  document.getElementById("expenseDate").value = today;
  document.getElementById("addExpenseModal").style.display = "block";
}

function showBudgetModal() {
  const modal = document.getElementById("budgetModal");
  if (modal) {
    modal.style.display = "block";
  }
}

// Expense Management Functions
function editExpense(expenseId) {
  // Fetch expense data and populate the edit modal
  fetch(`/get_expense/${expenseId}`)
    .then((response) => response.json())
    .then((expense) => {
      if (expense) {
        document.getElementById("editExpenseId").value = expense.id;
        document.getElementById("editExpenseDate").value = expense.date;
        document.getElementById("editExpenseDescription").value =
          expense.description;
        document.getElementById("editExpenseAmount").value = expense.amount;
        document.getElementById("editExpenseCategory").value =
          expense.category_id;

        // Clear all checkboxes first
        const checkboxes = document.querySelectorAll(
          '#editMemberCheckboxes input[type="checkbox"]'
        );
        checkboxes.forEach((cb) => (cb.checked = false));

        // Check the user checkbox if they participate
        if (expense.user_participates) {
          document.querySelector(
            '#editMemberCheckboxes input[name="include_user"]'
          ).checked = true;
        }

        // Check member checkboxes
        if (expense.member_ids) {
          expense.member_ids.forEach((memberId) => {
            const memberCheckbox = document.querySelector(
              `#editMemberCheckboxes input[value="${memberId}"]`
            );
            if (memberCheckbox) {
              memberCheckbox.checked = true;
            }
          });
        }

        document.getElementById("editExpenseModal").style.display = "block";
      }
    })
    .catch((error) => {
      console.error("Error fetching expense data:", error);
      alert("Error loading expense data");
    });
}

function deleteExpense(expenseId) {
  if (confirm("Are you sure you want to delete this expense?")) {
    fetch(`/delete_expense/${expenseId}`, {
      method: "POST",
    })
      .then((response) => {
        if (response.ok) {
          location.reload();
        } else {
          alert("Error deleting expense");
        }
      })
      .catch((error) => {
        console.error("Error deleting expense:", error);
        alert("Error deleting expense");
      });
  }
}

// Initialize All Event Listeners
document.addEventListener("DOMContentLoaded", function () {
  // Initialize event listeners for all buttons and interactive elements
  // (Removed) initializeEventListeners() was redundant after inlining listeners below

  // Initialize Charts if data exists
  if (typeof familyData !== "undefined") {
    // Initialize with family view
    createChart(
      "categoryChart",
      toChartDataset(familyData),
      "Family - Expense Categories"
    );
  }

  // Chart view toggle functionality (always set up; chart updates are guarded)
  const wholeFamilyBtn = document.getElementById("wholeFamilyBtn");
  const perMemberSelect = document.getElementById("perMemberSelect");
  const memberSelect =
    perMemberSelect || document.getElementById("memberSelect");

  if (wholeFamilyBtn && memberSelect) {
    wholeFamilyBtn.addEventListener("click", function () {
      // Update active state
      wholeFamilyBtn.classList.add("active");
      if (perMemberSelect) perMemberSelect.classList.remove("active");

      updateChart("family");
    });
  }

  if (memberSelect) {
    memberSelect.addEventListener("change", function () {
      // When a member is chosen, activate per-member view
      if (perMemberSelect) perMemberSelect.classList.add("active");
      wholeFamilyBtn && wholeFamilyBtn.classList.remove("active");
      updateChart("member");
    });
  }

  // Initialize Family Monthly Expenses Pie Chart (right chart)
  if (typeof familyData !== "undefined") {
    updatePieChart(familyData);
  }

  // Member dropdown functionality
  const memberDropdown = document.getElementById("memberDropdown");
  if (memberDropdown) {
    memberDropdown.addEventListener("click", function () {
      const menu = document.getElementById("memberDropdownMenu");
      if (menu) {
        menu.style.display = menu.style.display === "block" ? "none" : "block";
      }
    });
  }

  // Close modal when clicking outside (consolidated handler)
  window.onclick = function (event) {
    if (event.target.classList.contains("modal")) {
      event.target.style.display = "none";
    }
  };

  // Close dropdowns when clicking outside
  document.addEventListener("click", function (event) {
    if (!event.target.closest(".member-dropdown")) {
      const menu = document.getElementById("memberDropdownMenu");
      if (menu) menu.style.display = "none";
    }
  });

  // Initialize all event listeners that were previously in separate function
  // Header action buttons
  const addMemberBtn = document.querySelector('[data-action="add-member"]');
  const addExpenseBtn = document.querySelector('[data-action="add-expense"]');
  const manageBudgetBtn = document.querySelector(
    '[data-action="manage-budget"]'
  );

  if (addMemberBtn) addMemberBtn.addEventListener("click", showAddMemberModal);
  if (addExpenseBtn)
    addExpenseBtn.addEventListener("click", showAddExpenseModal);
  if (manageBudgetBtn) {
    manageBudgetBtn.addEventListener("click", function (e) {
      showBudgetModal();
    });
  }

  // Member action buttons (dynamic content)
  document.addEventListener("click", function (e) {
    // Handle member edit buttons
    if (e.target.matches('[data-action="edit-member"]')) {
      const memberId = e.target.dataset.memberId;
      const memberName = e.target.dataset.memberName;
      const memberRelationship = e.target.dataset.memberRelationship;
      editMember(memberId, memberName, memberRelationship);
    }

    // Handle member delete buttons
    if (e.target.matches('[data-action="delete-member"]')) {
      const memberId = e.target.dataset.memberId;
      const memberName = e.target.dataset.memberName;
      deleteMember(memberId, memberName);
    }

    // Handle expense edit buttons
    if (e.target.matches('[data-action="edit-expense"]')) {
      const expenseId = e.target.dataset.expenseId;
      editExpense(expenseId);
    }

    // Handle expense delete buttons
    if (e.target.matches('[data-action="delete-expense"]')) {
      const expenseId = e.target.dataset.expenseId;
      deleteExpense(expenseId);
    }

    // Handle add member card click
    if (e.target.matches(".add-member") || e.target.closest(".add-member")) {
      showAddMemberModal();
    }

    // Handle modal close buttons
    if (e.target.matches('[data-action="close-modal"]')) {
      const modalId = e.target.dataset.modalId;
      closeModal(modalId);
    }

    // Handle modal backdrop clicks
    if (e.target.matches(".modal")) {
      e.target.style.display = "none";
    }
  });

  // Add expense button in recent expenses section
  const addExpenseInSection = document.querySelector(
    '[data-action="add-expense-section"]'
  );
  if (addExpenseInSection)
    addExpenseInSection.addEventListener("click", showAddExpenseModal);

  // Form cancel buttons
  const cancelButtons = document.querySelectorAll('[data-action="cancel"]');
  cancelButtons.forEach((btn) => {
    btn.addEventListener("click", function () {
      const modalId = this.dataset.modalId;
      closeModal(modalId);
    });
  });
});
