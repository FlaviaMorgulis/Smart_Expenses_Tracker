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
    }).then((response) => {
      if (response.ok) {
        location.reload();
      } else {
        alert("Error deleting member");
      }
    });
  }
}

// Owner/User Profile Functions
function editProfile() {
  // Redirect to profile edit page or show modal
  alert("Edit Profile functionality - redirect to user profile page");
  // You can implement this to redirect to a profile page:
  // window.location.href = '/profile/edit';
}

function showSettings() {
  // Show settings modal or redirect to settings page
  alert("Settings functionality - show account settings");
  // You can implement this to show a settings modal or redirect:
  // window.location.href = '/settings';
}

// Member Dropdown Functionality (integrated as toggle-select)
document.addEventListener("DOMContentLoaded", function () {
  const memberSelect =
    document.getElementById("perMemberSelect") ||
    document.getElementById("memberSelect");

  if (memberSelect) {
    memberSelect.addEventListener("change", function () {
      const selectedMember = this.value;
      const memberName =
        this.options[this.selectedIndex]?.text || selectedMember;

      if (selectedMember && selectedMember !== "") {
        // Update chart or perform member-specific actions
        console.log(`Selected member: ${memberName} (ID: ${selectedMember})`);
      }
    });
  }
});

// Modal Functions (Member-specific)
function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.style.display = "none";
  }
}

// Close modals when clicking outside
window.addEventListener("click", function (event) {
  const modals = ["addMemberModal", "editMemberModal"];

  modals.forEach((modalId) => {
    const modal = document.getElementById(modalId);
    if (modal && event.target === modal) {
      modal.style.display = "none";
    }
  });
});

// Chart Management Functions
// Chart Management - Restore original single chart
let chartInstance;

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
    // Render a friendly placeholder message similar to dashboard when no data
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

  const chartConfig = {
    type: "doughnut",
    data: {
      labels: normalized.labels || [],
      datasets: [
        {
          data: normalized.values || [],
          backgroundColor:
            normalized.colors || generateColors(normalized.labels?.length || 0),
          borderWidth: 2,
          borderColor: "#fff",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        title: {
          display: true,
          text: chartTitle || "Expense Categories",
          font: { size: 16, weight: "bold" },
        },
        legend: {
          position: "bottom",
          labels: {
            padding: 20,
            usePointStyle: true,
            pointStyle: "circle",
            generateLabels: function (chart) {
              const data = chart.data;
              if (data.labels.length && data.datasets.length) {
                return data.labels.map((label, i) => {
                  const dataset = data.datasets[0];
                  const value = dataset.data[i];
                  const total = dataset.data.reduce((a, b) => a + b, 0);
                  const percentage =
                    total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                  return {
                    text: `${label}: $${value.toFixed(2)} (${percentage}%)`,
                    fillStyle: dataset.backgroundColor[i],
                    strokeStyle: dataset.borderColor,
                    lineWidth: dataset.borderWidth,
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
              const percentage =
                total > 0 ? ((value / total) * 100).toFixed(1) : 0;
              return `${label}: $${value.toFixed(2)} (${percentage}%)`;
            },
          },
        },
      },
      cutout: "50%",
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
  } else {
    createChart(
      "categoryChart",
      toChartDataset(familyData),
      "Family - Expense Categories"
    );
  }
}

function createFamilyChart(data) {
  console.log("createFamilyChart called with data:", data);

  if (familyChart) {
    familyChart.destroy();
  }

  const ctx = document.getElementById("familyChart").getContext("2d");

  // Default data if no data provided
  const defaultData = [
    { category: "Food", amount: 420 },
    { category: "Bills", amount: 320 },
    { category: "Transport", amount: 180 },
    { category: "Entertainment", amount: 125 },
  ];

  const chartData = data && data.length > 0 ? data : defaultData;
  console.log("Using family chart data:", chartData);

  familyChart = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: chartData.map((item) => item.category),
      datasets: [
        {
          data: chartData.map((item) => item.amount),
          backgroundColor: [
            "#4A90E2",
            "#50C878",
            "#FFB84D",
            "#E85D75",
            "#9B59B6",
            "#1ABC9C",
          ],
          borderWidth: 0,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "bottom",
          labels: { usePointStyle: true, padding: 15 },
        },
      },
    },
  });
}

function createMemberChart(data, memberName) {
  console.log(
    "createMemberChart called with data:",
    data,
    "for member:",
    memberName
  );

  if (memberChart) {
    memberChart.destroy();
  }

  const ctx = document.getElementById("memberChart").getContext("2d");

  // Default data if no data provided
  const defaultData = [{ category: "No Data", amount: 100 }];

  const chartData = data && data.length > 0 ? data : defaultData;
  console.log("Using member chart data:", chartData);

  memberChart = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: chartData.map((item) => item.category),
      datasets: [
        {
          data: chartData.map((item) => item.amount),
          backgroundColor:
            chartData.length === 1
              ? ["#E0E0E0"]
              : [
                  "#4A90E2",
                  "#50C878",
                  "#FFB84D",
                  "#E85D75",
                  "#9B59B6",
                  "#1ABC9C",
                ],
          borderWidth: 0,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "bottom",
          labels: { usePointStyle: true, padding: 15 },
        },
      },
    },
  });

  // Update the chart title
  const rightChartTitle = document.getElementById("rightChartTitle");
  if (rightChartTitle) {
    rightChartTitle.textContent = memberName || "Select a Member";
  }
}

function updateChartsBasedOnSelection(selectedValue) {
  console.log("Updating charts for selection:", selectedValue);

  if (selectedValue === "family") {
    // Show family data in left chart
    createFamilyChart(familyData);
    // Clear member chart or show placeholder
    createMemberChart([], "Select a Member");
  } else {
    // Show family data in left chart (always visible)
    createFamilyChart(familyData);
    // Show selected member data in right chart
    const memberData =
      (window.memberData && window.memberData[selectedValue]) || [];
    createMemberChart(memberData, selectedValue);
  }
}

// Modal Functions (Non-member modals)
function showAddExpenseModal() {
  // Set today's date as default
  const today = new Date().toISOString().split("T")[0];
  document.getElementById("expenseDate").value = today;
  document.getElementById("addExpenseModal").style.display = "block";
}

function showEditExpenseModal() {
  document.getElementById("editExpenseModal").style.display = "block";
}

function showBudgetModal() {
  document.getElementById("budgetModal").style.display = "block";
}

function showBudgetDetailsModal() {
  // For now, redirect to budget details or show the existing budget modal
  document.getElementById("budgetModal").style.display = "block";
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
    }).then((response) => {
      if (response.ok) {
        location.reload();
      } else {
        alert("Error deleting expense");
      }
    });
  }
}

// Member Dropdown Functions
function selectMember(memberId) {
  // Close dropdown
  const menu = document.getElementById("memberDropdownMenu");
  if (menu) {
    menu.style.display = "none";
  }

  if (memberId === "owner") {
    console.log("Selected owner");
    // Here you can add functionality for when owner is selected
  } else {
    console.log("Selected member:", memberId);
    // Here you can add functionality for when a specific member is selected
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

  // Initialize Family Monthly Comparison (right chart)
  const monthlyCanvas = document.getElementById("familyMonthlyComparisonChart");
  if (monthlyCanvas) {
    const ctx = monthlyCanvas.getContext("2d");
    const mc = Array.isArray(window.familyMonthlyComparison)
      ? window.familyMonthlyComparison
      : [];

    // Update months count badge
    const monthsCountEl = document.getElementById("familyMonthsCount");
    if (monthsCountEl) monthsCountEl.textContent = mc.length || 0;

    const labels = mc.map((d) => d.month_short);
    const incomeSeries = mc.map((d) => d.income);
    const expenseSeries = mc.map((d) => d.expenses);

    if (labels.length > 0) {
      new Chart(ctx, {
        type: "line",
        data: {
          labels,
          datasets: [
            {
              label: "Income",
              data: incomeSeries,
              borderColor: "#10B981",
              backgroundColor: "rgba(16,185,129,0.1)",
              tension: 0.4,
              fill: true,
            },
            {
              label: "Expenses",
              data: expenseSeries,
              borderColor: "#EF4444",
              backgroundColor: "rgba(239,68,68,0.1)",
              tension: 0.4,
              fill: true,
            },
          ],
        },
        options: {
          responsive: true,
          plugins: {
            legend: { position: "top" },
          },
          scales: {
            y: {
              beginAtZero: true,
              ticks: {
                callback: function (value) {
                  return "£" + value;
                },
              },
            },
          },
        },
      });
    } else {
      // Show an inline text message if there's no data
      ctx.font = "14px Arial";
      ctx.fillStyle = "#666";
      ctx.textAlign = "center";
      ctx.fillText("No monthly comparison data available", 200, 150);
    }
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

    // Close dropdown when clicking outside
    document.addEventListener("click", function (event) {
      if (!event.target.closest(".member-dropdown")) {
        const menu = document.getElementById("memberDropdownMenu");
        if (menu) {
          menu.style.display = "none";
        }
      }
    });
  }

  // Member card hover effects
  const memberCards = document.querySelectorAll(".member-card");
  memberCards.forEach((card) => {
    card.addEventListener("mouseenter", function () {
      const actions = this.querySelector(".member-actions");
      if (actions) {
        actions.style.opacity = "1";
      }
    });

    card.addEventListener("mouseleave", function () {
      const actions = this.querySelector(".member-actions");
      if (actions) {
        actions.style.opacity = "0";
      }
    });
  });

  // Close modal when clicking outside
  window.onclick = function (event) {
    if (event.target.classList.contains("modal")) {
      event.target.style.display = "none";
    }
  };

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
  if (manageBudgetBtn)
    manageBudgetBtn.addEventListener("click", showBudgetModal);

  // Owner/User action buttons
  const editProfileBtn = document.querySelector('[data-action="edit-profile"]');
  const settingsBtn = document.querySelector('[data-action="settings"]');

  if (editProfileBtn) editProfileBtn.addEventListener("click", editProfile);
  if (settingsBtn) settingsBtn.addEventListener("click", showSettings);

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
