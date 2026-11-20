// Invenpro Enterprise SaaS Client-Side Interaction & Real-Time Calculation Engine

// Shared Currency and Calculation Helpers
function getActiveCurrency() {
  return window.INVENPRO_CURRENCY || window.STOCKWISE_CURRENCY || '₹';
}

// 1. Auto-dismiss Django Alert Notifications after 5 seconds
function initAlerts() {
  const alerts = document.querySelectorAll('.alert-dismissible');
  alerts.forEach(function (alert) {
    if (alert.dataset.dismissInit) return;
    alert.dataset.dismissInit = 'true';
    setTimeout(function () {
      if (typeof bootstrap !== 'undefined' && bootstrap.Alert) {
        const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
        if (bsAlert) bsAlert.close();
      }
    }, 5000);
  });
}

// 2. Stock-In Real-Time Dynamic Calculations & Side Summary Panel
function initStockIn() {
  const productInSelect = document.getElementById('id_product_in');
  const qtyInInput = document.getElementById('id_quantity');
  const priceInInput = document.getElementById('id_unit_price');

  const summaryProdName = document.getElementById('summary_in_product_name');
  const summaryPrevStock = document.getElementById('summary_in_prev_stock');
  const summaryIncomingQty = document.getElementById('summary_in_incoming_qty');
  const summaryUpdatedStock = document.getElementById('summary_in_updated_stock');
  const summaryUnitPrice = document.getElementById('summary_in_unit_price');
  const summaryTotalCost = document.getElementById('summary_in_total_cost');
  const totalCalcPreview = document.getElementById('stock_in_total_preview');

  if (!productInSelect) return;

  function updateStockInSummary() {
    const currencySymbol = getActiveCurrency();
    const products = window.STOCKWISE_PRODUCTS || [];
    const selectedId = parseInt(productInSelect.value);
    const prod = products.find(p => p.id === selectedId);

    const qty = parseFloat(qtyInInput ? qtyInInput.value : 0) || 0;
    let price = parseFloat(priceInInput ? priceInInput.value : 0);

    if (prod) {
      const prevStock = parseFloat(prod.current_stock) || 0;
      const updatedStock = prevStock + qty;

      if (summaryProdName) summaryProdName.textContent = prod.name;
      if (summaryPrevStock) summaryPrevStock.textContent = prevStock.toFixed(2) + ' ' + prod.unit;
      if (summaryIncomingQty) summaryIncomingQty.textContent = '+ ' + qty.toFixed(2) + ' ' + prod.unit;
      if (summaryUpdatedStock) summaryUpdatedStock.textContent = updatedStock.toFixed(2) + ' ' + prod.unit;

      if (isNaN(price) || price === 0) {
        price = parseFloat(prod.purchase_price) || 0;
        if (priceInInput && (!priceInInput.value || parseFloat(priceInInput.value) === 0)) {
          priceInInput.value = prod.purchase_price;
        }
      }

      const total = (qty * price).toFixed(2);
      if (summaryUnitPrice) summaryUnitPrice.textContent = currencySymbol + ' ' + (price || 0).toFixed(2);
      if (summaryTotalCost) summaryTotalCost.textContent = currencySymbol + ' ' + total;
      if (totalCalcPreview) totalCalcPreview.textContent = currencySymbol + ' ' + total;
    } else {
      if (summaryProdName) summaryProdName.textContent = 'None selected';
      if (summaryPrevStock) summaryPrevStock.textContent = '0.00';
      if (summaryIncomingQty) summaryIncomingQty.textContent = '+ 0.00';
      if (summaryUpdatedStock) summaryUpdatedStock.textContent = '0.00';
      if (summaryTotalCost) summaryTotalCost.textContent = currencySymbol + ' 0.00';
      if (totalCalcPreview) totalCalcPreview.textContent = currencySymbol + ' 0.00';
    }
  }

  productInSelect.removeEventListener('change', updateStockInSummary);
  productInSelect.addEventListener('change', updateStockInSummary);
  if (qtyInInput) {
    qtyInInput.removeEventListener('input', updateStockInSummary);
    qtyInInput.addEventListener('input', updateStockInSummary);
  }
  if (priceInInput) {
    priceInInput.removeEventListener('input', updateStockInSummary);
    priceInInput.addEventListener('input', updateStockInSummary);
  }

  if (productInSelect.value) {
    updateStockInSummary();
  }
}

// 3. Stock-Out Real-Time Validation & Projected Remaining Stock
function initStockOut() {
  const productOutSelect = document.getElementById('id_product_out');
  const qtyOutInput = document.getElementById('id_quantity_out') || document.getElementById('id_quantity');

  const summaryOutProdName = document.getElementById('summary_out_product_name');
  const summaryOutAvailable = document.getElementById('summary_out_available');
  const summaryOutDeduct = document.getElementById('summary_out_deduct');
  const summaryOutRemaining = document.getElementById('summary_out_remaining');
  const stockOutWarning = document.getElementById('stock_out_warning');
  const submitOutBtn = document.getElementById('submit_stock_out_btn');

  if (!productOutSelect) return;

  function updateStockOutSummary() {
    const products = window.STOCKWISE_PRODUCTS || [];
    const selectedId = parseInt(productOutSelect.value);
    const prod = products.find(p => p.id === selectedId);

    const qty = parseFloat(qtyOutInput ? qtyOutInput.value : 0) || 0;

    if (prod) {
      const available = parseFloat(prod.current_stock) || 0;
      const remaining = available - qty;

      if (summaryOutProdName) summaryOutProdName.textContent = prod.name;
      if (summaryOutAvailable) summaryOutAvailable.textContent = available.toFixed(2) + ' ' + prod.unit;
      if (summaryOutDeduct) summaryOutDeduct.textContent = '- ' + qty.toFixed(2) + ' ' + prod.unit;

      if (summaryOutRemaining) {
        summaryOutRemaining.textContent = remaining.toFixed(2) + ' ' + prod.unit;
        if (remaining < 0) {
          summaryOutRemaining.className = 'fs-4 fw-bold text-danger';
        } else if (remaining <= parseFloat(prod.minimum_stock || 0)) {
          summaryOutRemaining.className = 'fs-4 fw-bold text-warning';
        } else {
          summaryOutRemaining.className = 'fs-4 fw-bold text-success';
        }
      }

      // Check negative stock violation
      if (qty > available) {
        if (stockOutWarning) {
          stockOutWarning.classList.remove('d-none');
          stockOutWarning.innerHTML = `<i class="bi bi-exclamation-triangle-fill me-1"></i> <strong>Exceeds Available Stock:</strong> You requested to deduct ${qty.toFixed(2)} ${prod.unit}, but only ${available.toFixed(2)} ${prod.unit} is available. Negative inventory is strictly prohibited.`;
        }
        if (submitOutBtn) submitOutBtn.disabled = true;
      } else {
        if (stockOutWarning) {
          stockOutWarning.classList.add('d-none');
        }
        if (submitOutBtn) submitOutBtn.disabled = false;
      }
    } else {
      if (summaryOutProdName) summaryOutProdName.textContent = 'None selected';
      if (summaryOutAvailable) summaryOutAvailable.textContent = '0.00';
      if (summaryOutDeduct) summaryOutDeduct.textContent = '- 0.00';
      if (summaryOutRemaining) summaryOutRemaining.textContent = '0.00';
      if (stockOutWarning) stockOutWarning.classList.add('d-none');
      if (submitOutBtn) submitOutBtn.disabled = false;
    }
  }

  productOutSelect.removeEventListener('change', updateStockOutSummary);
  productOutSelect.addEventListener('change', updateStockOutSummary);
  if (qtyOutInput) {
    qtyOutInput.removeEventListener('input', updateStockOutSummary);
    qtyOutInput.addEventListener('input', updateStockOutSummary);
  }

  if (productOutSelect.value) {
    updateStockOutSummary();
  }
}

// 4. Master Dynamic Components Initializer
function initDynamicComponents() {
  const prodDataEl = document.getElementById('stockwise-products-data');
  if (prodDataEl) {
    try {
      window.STOCKWISE_PRODUCTS = JSON.parse(prodDataEl.textContent || '[]');
    } catch (e) {
      window.STOCKWISE_PRODUCTS = [];
    }
  }
  initAlerts();
  initStockIn();
  initStockOut();
  if (typeof initDashboardCharts === 'function') {
    initDashboardCharts();
  }
  if (typeof initReportCharts === 'function') {
    initReportCharts();
  }
  if (typeof initStockAdj === 'function') {
    initStockAdj();
  }
}

// 5. Seamless Navigation Engine (Prevents Sidebar Reload & Flashing)
let isNavigating = false;

async function navigateSeamlessly(targetUrl, pushState = true) {
  if (isNavigating) return;

  const currentUrl = window.location.href;
  const targetObj = new URL(targetUrl, window.location.href);
  const currentObj = new URL(currentUrl, window.location.href);
  const resolvedUrl = targetObj.href;

  // If already at target URL (ignoring hash), just scroll top of content
  if (targetObj.pathname === currentObj.pathname && targetObj.search === currentObj.search) {
    const mainContent = document.querySelector('.app-content');
    if (mainContent) mainContent.scrollTo({ top: 0, behavior: 'smooth' });
    window.scrollTo({ top: 0, behavior: 'smooth' });
    return;
  }

  isNavigating = true;

  // Immediate visual feedback on sidebar: highlight clicked link
  const sidebarNav = document.querySelector('.sidebar-nav');
  if (sidebarNav) {
    const allLinks = sidebarNav.querySelectorAll('.nav-link');
    allLinks.forEach(function (l) {
      const linkObj = new URL(l.getAttribute('href'), window.location.origin);
      if (linkObj.pathname === targetObj.pathname) {
        l.classList.add('active');
      } else {
        l.classList.remove('active');
      }
    });
  }

  const appMain = document.querySelector('.app-main');
  if (appMain) {
    appMain.style.transition = 'opacity 0.12s ease';
    appMain.style.opacity = '0.7';
  }

  try {
    const response = await fetch(resolvedUrl, {
      headers: {
        'X-Requested-With': 'XMLHttpRequest'
      }
    });

    if (!response.ok) {
      window.location.href = resolvedUrl;
      return;
    }

    const htmlText = await response.text();
    const parser = new DOMParser();
    const doc = parser.parseFromString(htmlText, 'text/html');

    // 1. Update Title
    if (doc.title) {
      document.title = doc.title;
    }

    // 2. Update Content Area
    const newContent = doc.querySelector('.app-content');
    const curContent = document.querySelector('.app-content');
    if (newContent && curContent) {
      curContent.innerHTML = newContent.innerHTML;
    }

    // 3. Update Header (Restaurant ID, Bell badge, Dropdown)
    const newHeader = doc.querySelector('.app-header');
    const curHeader = document.querySelector('.app-header');
    if (newHeader && curHeader) {
      curHeader.innerHTML = newHeader.innerHTML;
    }

    // 4. Update Sidebar Low Stock Alert Count Bubble
    const newAlertBadge = doc.querySelector('.sidebar-nav a[href*="alerts"] .badge');
    const curAlertLink = document.querySelector('.sidebar-nav a[href*="alerts"]');
    if (curAlertLink) {
      const curBadge = curAlertLink.querySelector('.badge');
      if (newAlertBadge) {
        if (curBadge) {
          curBadge.textContent = newAlertBadge.textContent;
        } else {
          curAlertLink.insertAdjacentHTML('beforeend', newAlertBadge.outerHTML);
        }
      } else if (curBadge) {
        curBadge.remove();
      }
    }

    // 5. Update History
    if (pushState) {
      window.history.pushState({ path: resolvedUrl }, '', resolvedUrl);
    }

    // 6. Scroll content to top (main viewport only, NEVER touching sidebar scroll)
    const appContentElem = document.querySelector('.app-content');
    if (appContentElem) appContentElem.scrollTop = 0;
    window.scrollTo(0, 0);

    // 7. Extract and execute inline scripts from fetched page
    const fetchedScripts = doc.querySelectorAll('script');
    fetchedScripts.forEach(function (s) {
      // Execute page-specific inline scripts (e.g. from {% block extra_js %}), skipping JSON data blocks
      if (!s.src && s.textContent && s.type !== 'application/json') {
        // Avoid re-running global stockwise.js or bootstrap config
        if (!s.textContent.includes('stockwise.js') && !s.textContent.includes('sessionStorage.getItem')) {
          try {
            const scriptTag = document.createElement('script');
            scriptTag.textContent = s.textContent;
            document.body.appendChild(scriptTag);
            scriptTag.remove();
          } catch (err) {
            console.error('Error executing inline script:', err);
          }
        }
      }
    });

    // 8. Re-initialize dynamic components
    initDynamicComponents();

  } catch (err) {
    console.error('Seamless navigation error, fallback to full load:', err);
    window.location.href = targetUrl;
  } finally {
    if (appMain) {
      appMain.style.opacity = '1';
    }
    isNavigating = false;
  }
}

// 6. Main Document Ready Initialization
document.addEventListener('DOMContentLoaded', function () {
  // Sidebar Collapse / Expand via Logo & Hamburger Toggle
  const logoToggle = document.getElementById('sidebarLogoToggle');
  const toggleBtn = document.getElementById('sidebarToggle');
  const sidebar = document.querySelector('.app-sidebar');

  // Restore collapsed state from localStorage
  const savedCollapsed = localStorage.getItem('invenpro_sidebar_collapsed');
  if (savedCollapsed === 'true') {
    document.body.classList.add('sidebar-collapsed');
    document.documentElement.classList.add('sidebar-collapsed');
  }

  function toggleSidebarCollapse() {
    const isNowCollapsed = document.body.classList.toggle('sidebar-collapsed');
    document.documentElement.classList.toggle('sidebar-collapsed', isNowCollapsed);
    localStorage.setItem('invenpro_sidebar_collapsed', isNowCollapsed ? 'true' : 'false');
  }

  if (logoToggle) {
    logoToggle.addEventListener('click', function (e) {
      e.preventDefault();
      e.stopPropagation();
      toggleSidebarCollapse();
    });
  }

  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener('click', function (e) {
      e.stopPropagation();
      if (window.innerWidth <= 1024) {
        sidebar.classList.toggle('show');
      } else {
        toggleSidebarCollapse();
      }
    });

    document.addEventListener('click', function (e) {
      if (window.innerWidth <= 1024 && sidebar.classList.contains('show')) {
        if (!sidebar.contains(e.target) && e.target !== toggleBtn) {
          sidebar.classList.remove('show');
        }
      }
    });
  }

  // Sidebar Scroll Position Persistence & Mousewheel Isolation
  const sidebarNav = document.querySelector('.sidebar-nav');
  if (sidebarNav) {
    const savedPos = sessionStorage.getItem('invenpro_sidebar_scroll');
    if (savedPos !== null) {
      sidebarNav.scrollTop = parseInt(savedPos, 10);
    } else {
      const activeLink = sidebarNav.querySelector('.nav-link.active');
      if (activeLink) {
        activeLink.scrollIntoView({ block: 'nearest', behavior: 'instant' });
      }
    }

    let scrollDebounce;
    sidebarNav.addEventListener('scroll', function () {
      clearTimeout(scrollDebounce);
      scrollDebounce = setTimeout(function () {
        sessionStorage.setItem('invenpro_sidebar_scroll', sidebarNav.scrollTop);
      }, 50);
    }, { passive: true });

    sidebarNav.querySelectorAll('.nav-link').forEach(function (link) {
      link.addEventListener('click', function () {
        sessionStorage.setItem('invenpro_sidebar_scroll', sidebarNav.scrollTop);
      });
    });

    window.addEventListener('beforeunload', function () {
      sessionStorage.setItem('invenpro_sidebar_scroll', sidebarNav.scrollTop);
    });

    // Isolate Sidebar Scroll: Prevent mousewheel bleed to main page
    sidebarNav.addEventListener('wheel', function (e) {
      const delta = e.deltaY;
      sidebarNav.scrollTop += delta;
      sessionStorage.setItem('invenpro_sidebar_scroll', sidebarNav.scrollTop);
      e.preventDefault();
      e.stopPropagation();
    }, { passive: false });
  }

  // Intercept Navigation Clicks for Rock-Solid Persistent Sidebar
  document.body.addEventListener('click', function (e) {
    const link = e.target.closest('a');
    if (!link) return;

    const href = link.getAttribute('href');
    if (!href) return;

    // Filter out external or non-GET links
    if (
      href.startsWith('#') ||
      href.startsWith('javascript:') ||
      href.startsWith('mailto:') ||
      href.startsWith('tel:') ||
      link.target === '_blank' ||
      link.hasAttribute('download') ||
      link.dataset.noPjax !== undefined ||
      link.dataset.bsToggle !== undefined ||
      href.includes('/admin/') ||
      href.includes('toggle_theme') ||
      href.includes('logout')
    ) {
      return;
    }

    // Identify if this is a sidebar link, header bell, or internal navigation / pagination link
    const isSidebarLink = link.closest('.app-sidebar');
    const isHeaderBell = link.closest('.header-bell-btn');
    const isInternalGet = (href.startsWith('/') && !href.startsWith('//')) || href.startsWith('?');

    if (isSidebarLink || isHeaderBell || (isInternalGet && link.closest('.app-content'))) {
      e.preventDefault();
      navigateSeamlessly(href, true);
    }
  });

  // Delegated UI Handlers for Admin Management (Password Eye Toggle & Edit Modal)
  document.body.addEventListener('click', function (e) {
    // 1. Toggle password visibility in Admins Roster table row
    const rowEyeBtn = e.target.closest('.btn-toggle-pwd-row');
    if (rowEyeBtn) {
      e.preventDefault();
      const box = rowEyeBtn.closest('.password-reveal-box');
      const textEl = box ? box.querySelector('.password-reveal-text') : null;
      const iconEl = rowEyeBtn.querySelector('i');
      if (textEl) {
        const isMasked = textEl.dataset.masked === 'true';
        if (isMasked) {
          textEl.textContent = textEl.dataset.password || '';
          textEl.dataset.masked = 'false';
          if (iconEl) iconEl.className = 'bi bi-eye-slash-fill text-warning';
        } else {
          textEl.textContent = '••••••••';
          textEl.dataset.masked = 'true';
          if (iconEl) iconEl.className = 'bi bi-eye';
        }
      }
      return;
    }

    // 2. Toggle password visibility inside modal password input
    const inputEyeBtn = e.target.closest('.btn-toggle-pwd-input');
    if (inputEyeBtn) {
      e.preventDefault();
      const targetId = inputEyeBtn.dataset.target;
      const inputEl = targetId ? document.getElementById(targetId) : null;
      const iconEl = inputEyeBtn.querySelector('i');
      if (inputEl) {
        if (inputEl.type === 'password') {
          inputEl.type = 'text';
          if (iconEl) iconEl.className = 'bi bi-eye-slash-fill text-warning';
        } else {
          inputEl.type = 'password';
          if (iconEl) iconEl.className = 'bi bi-eye';
        }
      }
      return;
    }

    // 3. Populate Edit Admin Details & Password Modal
    const editBtn = e.target.closest('.btn-edit-admin');
    if (editBtn) {
      const form = document.getElementById('editAdminForm');
      const unameInput = document.getElementById('editAdminUsername');
      const fnInput = document.getElementById('editAdminFirstName');
      const lnInput = document.getElementById('editAdminLastName');
      const emailInput = document.getElementById('editAdminEmail');
      const phoneInput = document.getElementById('editAdminPhone');
      const statusWrap = document.getElementById('editAdminStatusWrap');
      const statusSelect = document.getElementById('editAdminStatus');
      const pwdInput = document.getElementById('editAdminNewPassword');
      const pwdHint = document.getElementById('editAdminCurrentPwdHint');

      if (form) form.action = editBtn.dataset.action || '';
      if (unameInput) unameInput.value = editBtn.dataset.username || '';
      if (fnInput) fnInput.value = editBtn.dataset.firstName || '';
      if (lnInput) lnInput.value = editBtn.dataset.lastName || '';
      if (emailInput) emailInput.value = editBtn.dataset.email || '';
      if (phoneInput) phoneInput.value = editBtn.dataset.phone || '';

      if (statusWrap && statusSelect) {
        if (editBtn.dataset.isSelf === 'true') {
          statusWrap.classList.add('d-none');
        } else {
          statusWrap.classList.remove('d-none');
          statusSelect.value = editBtn.dataset.isActive === 'false' ? 'false' : 'true';
        }
      }

      if (pwdInput) {
        pwdInput.value = '';
        pwdInput.type = 'password';
        const toggleIcon = document.querySelector('.btn-toggle-pwd-input[data-target="editAdminNewPassword"] i');
        if (toggleIcon) toggleIcon.className = 'bi bi-eye';
        if (editBtn.dataset.focusPwd === 'true') {
          setTimeout(function () { pwdInput.focus(); }, 300);
        }
      }

      if (pwdHint) {
        const curPwd = editBtn.dataset.currentPwd || '';
        if (curPwd) {
          pwdHint.classList.remove('d-none');
          pwdHint.innerHTML = '<i class="bi bi-info-circle me-1"></i>A password is already recorded. Enter a new password above to replace it.';
        } else {
          pwdHint.classList.remove('d-none');
          pwdHint.innerHTML = '<i class="bi bi-info-circle me-1"></i>No visible password recorded yet. Set a new password here to enable the eye-button preview.';
        }
      }
    }
  });

  // Interactive Auth Stage: Guest Theme Toggle, Dynamic Greeting, Cursor Glow & 6-Box OTP
  function initAuthInteractions() {
    // 1. Guest Light / Dark Theme Toggle Switch
    const guestToggleBtn = document.getElementById('guestThemeToggleBtn');
    const guestThemeLabel = document.getElementById('guestThemeLabel');

    function syncGuestThemeLabel() {
      const active = document.documentElement.getAttribute('data-bs-theme') || 'light';
      if (guestThemeLabel) {
        guestThemeLabel.textContent = active === 'dark' ? 'Dark' : 'Light';
      }
    }
    syncGuestThemeLabel();

    if (guestToggleBtn) {
      guestToggleBtn.addEventListener('click', function () {
        const current = document.documentElement.getAttribute('data-bs-theme') || 'light';
        const nextTheme = current === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-bs-theme', nextTheme);
        localStorage.setItem('invenpro_guest_theme', nextTheme);
        syncGuestThemeLabel();

        const toggleUrl = guestToggleBtn.dataset.toggleUrl;
        if (toggleUrl) {
          fetch(toggleUrl + '?mode=' + encodeURIComponent(nextTheme), {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
          }).catch(function () {});
        }
      });
    }

    // 2. Pleasant Time-of-Day Greeting
    const greetingEl = document.getElementById('authDynamicGreeting');
    if (greetingEl) {
      const hr = new Date().getHours();
      if (hr < 12) {
        greetingEl.textContent = 'Good Morning · Ready for Today';
      } else if (hr < 17) {
        greetingEl.textContent = 'Good Afternoon · Smooth Operations';
      } else {
        greetingEl.textContent = 'Good Evening · Evening Service Ready';
      }
    }

    // 3. Subtle Interactive Cursor Spotlight Glow on Auth Stage
    const authStage = document.querySelector('.auth-stage');
    const cursorGlow = document.getElementById('authCursorGlow');
    if (authStage && cursorGlow) {
      authStage.addEventListener('mousemove', function (e) {
        cursorGlow.style.opacity = '1';
        cursorGlow.style.left = e.clientX + 'px';
        cursorGlow.style.top = e.clientY + 'px';
      });
      authStage.addEventListener('mouseleave', function () {
        cursorGlow.style.opacity = '0';
      });
    }

    // 4. Interactive 6-Box OTP Input (Auto-advance, Backspace & Paste)
    const otpGroup = document.getElementById('otpDigitsGroup');
    const otpHidden = document.getElementById('otpCodeHidden');
    const otpForm = document.getElementById('otpVerifyForm');
    if (otpGroup && otpHidden) {
      const inputs = Array.from(otpGroup.querySelectorAll('.otp-digit-input'));

      function syncOtpHidden() {
        otpHidden.value = inputs.map(function (inp) { return inp.value.replace(/\D/g, ''); }).join('');
      }

      inputs.forEach(function (inp, idx) {
        inp.addEventListener('input', function () {
          const clean = inp.value.replace(/\D/g, '');
          inp.value = clean.slice(-1);
          syncOtpHidden();
          if (inp.value && idx < inputs.length - 1) {
            inputs[idx + 1].focus();
          }
        });

        inp.addEventListener('keydown', function (e) {
          if (e.key === 'Backspace' && !inp.value && idx > 0) {
            inputs[idx - 1].focus();
          }
        });

        inp.addEventListener('paste', function (e) {
          e.preventDefault();
          const pasted = ((e.clipboardData || window.clipboardData).getData('text') || '').replace(/\D/g, '').slice(0, inputs.length);
          for (let i = 0; i < inputs.length; i++) {
            inputs[i].value = pasted[i] || '';
          }
          syncOtpHidden();
          const focusIdx = Math.min(pasted.length, inputs.length - 1);
          inputs[focusIdx].focus();
        });
      });

      if (otpForm) {
        otpForm.addEventListener('submit', function () {
          syncOtpHidden();
        });
      }
    }
  }
  initAuthInteractions();

  // Handle Browser Back / Forward Buttons via popstate
  window.addEventListener('popstate', function () {
    navigateSeamlessly(window.location.href, false);
  });

  // Initial Run of Page Components
  initDynamicComponents();
});
