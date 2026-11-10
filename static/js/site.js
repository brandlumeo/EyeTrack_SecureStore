(() => {
    const root = document.documentElement;
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const STORAGE_KEYS = {
        wishlist: 'ets_wishlist_v1',
        compare: 'ets_compare_v1',
    };
    const COOKIE_KEYS = {
        wishlist: 'ets_wishlist_ck',
        compare: 'ets_compare_ck',
    };
    const memoryStore = {
        wishlist: [],
        compare: [],
    };

    const readCookieJson = (name) => {
        const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`));
        if (!match) return null;
        try {
            const parsed = JSON.parse(decodeURIComponent(match[1]));
            return Array.isArray(parsed) ? parsed : null;
        } catch {
            return null;
        }
    };

    const writeCookieJson = (name, value) => {
        try {
            const encoded = encodeURIComponent(JSON.stringify(value));
            document.cookie = `${name}=${encoded}; Path=/; Max-Age=2592000; SameSite=Lax`;
        } catch {
            // Ignore serialization/cookie failures.
        }
    };

    const getCollection = (type) => {
        try {
            const parsed = JSON.parse(localStorage.getItem(STORAGE_KEYS[type]) || '[]');
            if (Array.isArray(parsed) && parsed.length) {
                return parsed;
            }
            const cookieValue = readCookieJson(COOKIE_KEYS[type]);
            return cookieValue || (Array.isArray(parsed) ? parsed : []);
        } catch {
            const cookieValue = readCookieJson(COOKIE_KEYS[type]);
            return cookieValue || (Array.isArray(memoryStore[type]) ? memoryStore[type] : []);
        }
    };

    const setCollection = (type, items) => {
        memoryStore[type] = Array.isArray(items) ? items : [];
        writeCookieJson(COOKIE_KEYS[type], memoryStore[type]);
        try {
            localStorage.setItem(STORAGE_KEYS[type], JSON.stringify(memoryStore[type]));
        } catch {
            // Fallback to in-memory state when browser storage is blocked.
        }
    };

    const getCookie = (name) => {
        const cookieMatch = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`));
        return cookieMatch ? decodeURIComponent(cookieMatch[1]) : '';
    };

    const markReady = () => {
        root.classList.remove('ui-booting');
        root.classList.add('ui-ready');

        const revealItems = document.querySelectorAll('.reveal');
        if (revealItems.length && 'IntersectionObserver' in window) {
            const revealObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('in-view');
                        observer.unobserve(entry.target);
                    }
                });
            }, { threshold: 0.12, rootMargin: '0px 0px -8% 0px' });

            revealItems.forEach((item, index) => {
                item.style.transitionDelay = `${Math.min(index * 45, 260)}ms`;
                revealObserver.observe(item);
            });
        } else {
            revealItems.forEach((item) => item.classList.add('in-view'));
        }
    };

    const startLeaving = () => {
        if (!root.classList.contains('is-leaving')) {
            root.classList.add('is-leaving');
        }
    };
    const clearLeavingState = () => {
        root.classList.remove('is-leaving');
    };

    const setupPremiumToast = () => {
        const toastEl = document.getElementById('premiumActionToast');
        const toastText = document.getElementById('premiumToastText');
        const toastIcon = document.getElementById('premiumToastIcon');
        if (!toastEl || typeof bootstrap === 'undefined') {
            return () => { };
        }
        const toast = bootstrap.Toast.getOrCreateInstance(toastEl);
        return (message, kind = 'success') => {
            if (toastText) {
                toastText.textContent = message;
            }
            if (toastIcon) {
                toastIcon.className = kind === 'error' ? 'bi bi-x-circle-fill' : 'bi bi-check-circle-fill';
                toastIcon.style.color = kind === 'error' ? '#ffb2bf' : '#7de7a5';
            }
            toast.show();
        };
    };

    const setupPageTransitionHooks = () => {
        const forceClear = () => {
            clearLeavingState();
            document.body.offsetHeight; // force reflow
            setTimeout(clearLeavingState, 50);
        };

        window.addEventListener('pageshow', (event) => {
            forceClear();
            if (event.persisted) {
                setTimeout(forceClear, 300);
            }
        });

        window.addEventListener('pagehide', clearLeavingState);
        window.addEventListener('popstate', forceClear);

        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'visible' || document.visibilityState === 'hidden') {
                forceClear();
            }
        });
    };

    const setupCatalogFiltersLayout = () => {
        const filtersPanel = document.getElementById('mobileFilters');
        const catalogGridCol = document.getElementById('catalogGridCol');
        const filtersToggleIcon = document.getElementById('filtersToggleIcon');
        if (!filtersPanel || !catalogGridCol) {
            return;
        }

        const syncCatalogLayout = () => {
            const expanded = filtersPanel.classList.contains('show');
            catalogGridCol.classList.toggle('col-lg-12', !expanded);
            catalogGridCol.classList.toggle('col-lg-9', expanded);
            if (filtersToggleIcon) {
                filtersToggleIcon.classList.toggle('bi-chevron-up', expanded);
                filtersToggleIcon.classList.toggle('bi-chevron-down', !expanded);
            }
        };

        syncCatalogLayout();
        filtersPanel.addEventListener('shown.bs.collapse', syncCatalogLayout);
        filtersPanel.addEventListener('hidden.bs.collapse', syncCatalogLayout);
    };

    const setupMobileFilterUx = () => {
        const form = document.getElementById('catalogFilterForm');
        if (!form) {
            return;
        }
        const badges = [
            document.getElementById('mobileFilterCount'),
            document.getElementById('mobileFilterCountDock'),
        ].filter(Boolean);

        const countActive = () => {
            let count = 0;
            const qValue = (form.querySelector('[name="q"]')?.value || '').trim();
            const minValue = (form.querySelector('[name="min_price"]')?.value || '').trim();
            const maxValue = (form.querySelector('[name="max_price"]')?.value || '').trim();
            const stockChecked = form.querySelector('[name="in_stock"]')?.checked;
            const sortValue = form.querySelector('[name="sort"]')?.value || 'featured';
            if (qValue) count += 1;
            if (minValue) count += 1;
            if (maxValue) count += 1;
            if (stockChecked) count += 1;
            if (sortValue !== 'featured') count += 1;
            badges.forEach((badge) => {
                badge.textContent = `${count}`;
                badge.style.opacity = count > 0 ? '1' : '0.65';
            });
        };

        form.addEventListener('input', countActive);
        form.addEventListener('change', countActive);
        countActive();
    };

    const setupProductCardNavigation = () => {
        document.addEventListener('click', (event) => {
            const card = event.target.closest('.product-card[data-href]');
            if (!card) {
                return;
            }
            if (event.target.closest('a, button, .btn, input, select, textarea, label, form')) {
                return;
            }
            const href = card.dataset.href;
            if (href) {
                window.location.href = href;
            }
        });

        document.addEventListener('keydown', (event) => {
            const card = event.target.closest('.product-card[data-href]');
            if (!card) {
                return;
            }
            if (event.key !== 'Enter' && event.key !== ' ') {
                return;
            }
            event.preventDefault();
            const href = card.dataset.href;
            if (href) {
                window.location.href = href;
            }
        });
    };

    const setupSmartScrollUI = () => {
        const progressBar = document.getElementById('scrollProgressBar');
        const header = document.getElementById('siteHeader');
        const backToTopBtn = document.getElementById('backToTopBtn');
        const heroLayers = Array.from(document.querySelectorAll('.hero-live-bg'));
        let ticking = false;

        const updateScrollUI = () => {
            const scrollTop = window.scrollY || document.documentElement.scrollTop || 0;
            const maxScroll = Math.max(document.documentElement.scrollHeight - window.innerHeight, 1);
            const progress = Math.min((scrollTop / maxScroll) * 100, 100);

            if (progressBar) {
                progressBar.style.width = `${progress}%`;
            }
            if (header) {
                header.classList.toggle('is-scrolled', scrollTop > 24);
            }
            if (backToTopBtn) {
                backToTopBtn.classList.toggle('is-visible', scrollTop > 420);
            }

            if (!prefersReducedMotion && heroLayers.length) {
                heroLayers.forEach((layer) => {
                    const hero = layer.closest('.hero-live');
                    if (!hero) {
                        return;
                    }
                    const rect = hero.getBoundingClientRect();
                    if (rect.bottom < -80 || rect.top > window.innerHeight + 80) {
                        return;
                    }
                    const ratio = (window.innerHeight - rect.top) / (window.innerHeight + rect.height);
                    const shiftY = (ratio - 0.5) * 14;
                    layer.style.transform = `translate3d(0, ${shiftY.toFixed(2)}px, 0)`;
                });
            }

            ticking = false;
        };

        const onScroll = () => {
            if (!ticking) {
                ticking = true;
                window.requestAnimationFrame(updateScrollUI);
            }
        };

        window.addEventListener('scroll', onScroll, { passive: true });
        window.addEventListener('resize', onScroll);

        if (backToTopBtn) {
            backToTopBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                try {
                    window.scroll({ top: 0, left: 0, behavior: 'smooth' });
                } catch (err) {
                    window.scrollTo(0, 0);
                }
            });
        }

        onScroll();
    };

    const setupAnchorScrolling = () => {
        const navLinks = Array.from(document.querySelectorAll('a[href^="#"]'))
            .filter((link) => {
                const href = link.getAttribute('href') || '';
                return href.length > 1 && !href.startsWith('#!');
            });

        if (!navLinks.length) {
            return;
        }

        const targetMap = new Map();
        navLinks.forEach((link) => {
            const id = (link.getAttribute('href') || '').slice(1);
            if (!id) {
                return;
            }
            const target = document.getElementById(id);
            if (!target) {
                return;
            }
            if (!targetMap.has(id)) {
                targetMap.set(id, { element: target, links: [] });
            }
            targetMap.get(id).links.push(link);
            link.addEventListener('click', (event) => {
                const href = link.getAttribute('href') || '';
                if (!href.startsWith('#')) {
                    return;
                }
                event.preventDefault();
                target.scrollIntoView({ behavior: prefersReducedMotion ? 'auto' : 'smooth', block: 'start' });
                history.replaceState(null, '', `${window.location.pathname}${window.location.search}#${id}`);
            });
        });

        if (!targetMap.size || !('IntersectionObserver' in window)) {
            return;
        }

        const allLinks = Array.from(targetMap.values()).flatMap((item) => item.links);
        const clearActiveLinks = () => {
            allLinks.forEach((link) => link.classList.remove('is-section-active'));
        };

        const sectionObserver = new IntersectionObserver((entries) => {
            const visible = entries
                .filter((entry) => entry.isIntersecting)
                .sort((a, b) => b.intersectionRatio - a.intersectionRatio);
            if (!visible.length) {
                return;
            }
            const activeId = visible[0].target.id;
            clearActiveLinks();
            const targetEntry = targetMap.get(activeId);
            if (targetEntry) {
                targetEntry.links.forEach((link) => link.classList.add('is-section-active'));
            }
        }, { threshold: [0.3, 0.55], rootMargin: '-15% 0px -55% 0px' });

        targetMap.forEach((item) => sectionObserver.observe(item.element));
    };

    const setupCardTilt = () => {
        if (prefersReducedMotion || window.matchMedia('(pointer: coarse)').matches) {
            return;
        }
        const cards = document.querySelectorAll('.product-card');
        cards.forEach((card) => {
            const resetTilt = () => {
                card.style.setProperty('--tilt-x', '0deg');
                card.style.setProperty('--tilt-y', '0deg');
                card.classList.remove('is-tilting');
            };

            card.addEventListener('pointermove', (event) => {
                const rect = card.getBoundingClientRect();
                const relX = (event.clientX - rect.left) / rect.width;
                const relY = (event.clientY - rect.top) / rect.height;
                const tiltY = (relX - 0.5) * 7;
                const tiltX = (0.5 - relY) * 7;
                card.classList.add('is-tilting');
                card.style.setProperty('--tilt-x', `${tiltX.toFixed(2)}deg`);
                card.style.setProperty('--tilt-y', `${tiltY.toFixed(2)}deg`);
            });

            card.addEventListener('pointerleave', resetTilt);
            card.addEventListener('blur', resetTilt, true);
        });
    };

    const setupQuickCartDrawer = (showToast) => {
        const drawerEl = document.getElementById('quickCartDrawer');
        if (!drawerEl || typeof bootstrap === 'undefined') {
            return;
        }

        const drawer = bootstrap.Offcanvas.getOrCreateInstance(drawerEl);
        const countBadges = document.querySelectorAll('[data-cart-count]');
        const quickCartName = document.getElementById('quickCartName');
        const quickCartPrice = document.getElementById('quickCartPrice');
        const quickCartQty = document.getElementById('quickCartQty');
        const quickCartImage = document.getElementById('quickCartImage');
        const quickCartFallback = document.getElementById('quickCartFallback');
        const quickCartMessage = document.getElementById('quickCartMessage');

        const updateBadgeCount = (count) => {
            countBadges.forEach((badge) => {
                badge.textContent = `${count}`;
            });
        };

        document.addEventListener('submit', async (event) => {
            const form = event.target;
            if (!(form instanceof HTMLFormElement)) {
                return;
            }
            if (!form.action || !form.action.includes('add-to-cart')) {
                return;
            }
            // If this is the product-list upsell form, let the installation modal handle it
            if (form.classList.contains('add-to-cart-form')) {
                return;
            }
            event.preventDefault();
            const submitButton = form.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.disabled = true;
            }
            try {
                const response = await fetch(form.action, {
                    method: 'POST',
                    body: new FormData(form),
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'Accept': 'application/json',
                    },
                });
                const data = await response.json();
                if (!response.ok || !data.ok) {
                    quickCartMessage.textContent = data.message || 'Unable to add item to cart.';
                    showToast(data.message || 'Unable to add item to cart.', 'error');
                    drawer.show();
                    return;
                }

                if (data.item) {
                    if (quickCartName) quickCartName.textContent = data.item.name || 'Item added';
                    if (quickCartPrice) quickCartPrice.textContent = data.item.price ? `Rs ${data.item.price}` : '';
                    if (quickCartQty) quickCartQty.textContent = `Qty in cart: ${data.item.quantity || 1}`;
                    if (quickCartMessage) quickCartMessage.textContent = data.message || 'Item added to cart.';

                    if (quickCartImage && quickCartFallback) {
                        if (data.item.image) {
                            quickCartImage.src = data.item.image;
                            quickCartImage.alt = data.item.name || 'Product image';
                            quickCartImage.classList.remove('d-none');
                            quickCartFallback.classList.add('d-none');
                        } else {
                            quickCartImage.classList.add('d-none');
                            quickCartFallback.classList.remove('d-none');
                        }
                    }
                }

                if (typeof data.cart_count !== 'undefined') {
                    updateBadgeCount(data.cart_count);
                }
                showToast(data.message || 'Item added to cart.');
                drawer.show();
            } catch (error) {
                form.submit();
            } finally {
                if (submitButton) {
                    submitButton.disabled = false;
                }
            }
        });
    };

    const setupQuickView = () => {
        const modalEl = document.getElementById('quickViewModal');
        if (!modalEl || typeof bootstrap === 'undefined') {
            return;
        }
        const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
        const quickViewLoading = document.getElementById('quickViewLoading');
        const quickViewImage = document.getElementById('quickViewImage');
        const quickViewFallback = document.getElementById('quickViewFallback');
        const quickViewCategory = document.getElementById('quickViewCategory');
        const quickViewName = document.getElementById('quickViewName');
        const quickViewPrice = document.getElementById('quickViewPrice');
        const quickViewStock = document.getElementById('quickViewStock');
        const quickViewDescription = document.getElementById('quickViewDescription');
        const quickViewDetailLink = document.getElementById('quickViewDetailLink');
        const quickViewAddForm = document.getElementById('quickViewAddForm');
        const quickViewSpecsContainer = document.getElementById('quickViewSpecsContainer');
        const quickViewSpecsGrid = document.getElementById('quickViewSpecsGrid');

        document.addEventListener('click', async (event) => {
            const btn = event.target.closest('.quick-view-btn');
            if (!btn) {
                return;
            }
            event.preventDefault();
            const productId = btn.dataset.productId;
            if (!productId) {
                return;
            }

            // Show loading state
            if (quickViewLoading) quickViewLoading.classList.remove('d-none');
            modal.show();

            try {
                const response = await fetch(`/api/product/${productId}/quick-view/`, {
                    headers: { 'Accept': 'application/json' },
                });
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                const data = await response.json();
                if (!data.ok || !data.product) {
                    throw new Error('Product data not found');
                }
                
                const product = data.product;
                
                // Populate basic info
                quickViewCategory.textContent = product.category || 'Product';
                quickViewName.textContent = product.name || 'Product';
                quickViewPrice.textContent = product.price ? `Rs ${product.price}` : '';
                
                // Stock status
                if (quickViewStock) {
                    if (product.stock <= 0) {
                        quickViewStock.innerHTML = `<i class="bi bi-x-circle-fill me-1"></i>Out of Stock`;
                        quickViewStock.className = `stock-status-badge small out-of-stock`;
                    } else if (product.stock <= 5) {
                        quickViewStock.innerHTML = `<i class="bi bi-fire me-1"></i>Low Stock: ${product.stock} Left`;
                        quickViewStock.className = `stock-status-badge small low-stock`;
                    } else {
                        quickViewStock.innerHTML = `<i class="bi bi-check-circle-fill me-1"></i>In Stock: ${product.stock}`;
                        quickViewStock.className = `stock-status-badge small in-stock`;
                    }
                }

                quickViewDescription.textContent = product.description || '';
                quickViewDetailLink.href = product.url || '#';
                
                if (quickViewAddForm && product.add_to_cart_url) {
                    quickViewAddForm.setAttribute('action', product.add_to_cart_url);
                }

                // Populate Image
                if (product.image) {
                    quickViewImage.src = product.image;
                    quickViewImage.alt = product.name || 'Product image';
                    quickViewImage.classList.remove('d-none');
                    quickViewFallback.classList.add('d-none');
                } else {
                    quickViewImage.classList.add('d-none');
                    quickViewFallback.classList.remove('d-none');
                }

                // Populate Specs
                if (quickViewSpecsGrid && product.display_specs && product.display_specs.length > 0) {
                    quickViewSpecsGrid.innerHTML = '';
                    // Limit to top 4 key specs for quick view
                    product.display_specs.slice(0, 4).forEach(spec => {
                        const specHtml = `
                            <div class="quick-view-spec-item">
                                <span class="quick-view-spec-label">${spec.label}</span>
                                <span class="quick-view-spec-value">${spec.value}</span>
                            </div>
                        `;
                        quickViewSpecsGrid.insertAdjacentHTML('beforeend', specHtml);
                    });
                    quickViewSpecsContainer.classList.remove('d-none');
                } else {
                    quickViewSpecsContainer.classList.add('d-none');
                }

            } catch (error) {
                console.error('Quick view fetch failed:', error);
                modal.hide();
                if (typeof showPremiumToast === 'function') {
                    showPremiumToast('Unable to load product preview', 'error');
                }
            } finally {
                if (quickViewLoading) quickViewLoading.classList.add('d-none');
            }
        });
    };


    const setupWishlistCompare = (showToast) => {
        const maxCompare = 4;
        const wishlistItems = document.getElementById('wishlistItems');
        const compareItems = document.getElementById('compareItems');
        const wishlistEmpty = document.getElementById('wishlistEmpty');
        const compareEmpty = document.getElementById('compareEmpty');
        const clearWishlistBtn = document.getElementById('clearWishlistBtn');
        const clearCompareBtn = document.getElementById('clearCompareBtn');
        const wishlistCountEls = document.querySelectorAll('[data-wishlist-count]');
        const compareCountEls = document.querySelectorAll('[data-compare-count]');
        const wishlistDrawerEl = document.getElementById('wishlistDrawer');
        const compareDrawerEl = document.getElementById('compareDrawer');
        const wishlistToggleBtn = document.getElementById('wishlistToggleBtn');
        const compareToggleBtn = document.getElementById('compareToggleBtn');

        const toggleCollection = async (type, btn) => {
            const config = window.EyetrackConfig || {};
            const productId = btn.dataset.productId || btn.getAttribute('data-product-id') || '';
            const productData = {
                id: productId,
                name: btn.dataset.productName || btn.getAttribute('data-product-name') || 'Product',
                price: btn.dataset.productPrice || btn.getAttribute('data-product-price') || '',
                url: btn.dataset.productUrl || btn.getAttribute('data-product-url') || '#',
                image: btn.dataset.productImage || btn.getAttribute('data-product-image') || '',
                category: btn.dataset.productCategory || btn.getAttribute('data-product-category') || '',
            };

            if (!productId) {
                return;
            }

            const currentItems = getCollection(type);
            const exists = currentItems.some((item) => String(item.id) === String(productId));
            let nextItems = [];

            if (exists) {
                nextItems = currentItems.filter((item) => String(item.id) !== String(productId));
                showToast(`Removed from ${type}.`);
            } else {
                if (type === 'compare' && currentItems.length >= 4) {
                    showToast('Comparison limit reached (max 4).', 'warning');
                    return;
                }
                nextItems = [...currentItems, productData];
                showToast(`Added to ${type}.`);
            }

            setCollection(type, nextItems);

            // Server-side sync for wishlist if authenticated
            if (type === 'wishlist' && config.isAuthenticated) {
                try {
                    const response = await fetch(`${config.toggleWishlistUrl}${productId}/`, {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': config.csrfToken,
                            'X-Requested-With': 'XMLHttpRequest',
                        }
                    });
                    const data = await response.json();
                    if (data.ok) {
                        // Ensure badge counts match server exactly
                        const wishlistBadges = document.querySelectorAll('[data-wishlist-count]');
                        wishlistBadges.forEach(el => el.textContent = data.wishlist_count);
                    }
                } catch (error) {
                    console.error('Wishlist server sync failed:', error);
                }
            }

            renderCollection(type);
            updateCounts();
            syncButtonStates();
        };

        const renderCollection = (type) => {
            const items = getCollection(type);
            const host = type === 'wishlist' ? wishlistItems : compareItems;
            const emptyEl = type === 'wishlist' ? wishlistEmpty : compareEmpty;
            if (!host || !emptyEl) {
                return;
            }
            host.innerHTML = '';
            if (!items.length) {
                emptyEl.classList.remove('d-none');
            } else {
                emptyEl.classList.add('d-none');
                items.forEach((item) => {
                    const row = document.createElement('div');
                    row.className = 'quick-saved-item';
                    const thumbSrc = item.image || 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw==';
                    row.innerHTML = `
                        <img class="quick-saved-thumb" src="${thumbSrc}" alt="${item.name}">
                        <div class="quick-saved-meta">
                            <a href="${item.url}">${item.name}</a>
                            <p>${item.price ? `Rs ${item.price}` : ''}</p>
                        </div>
                        <button type="button" class="btn btn-sm btn-outline-danger remove-saved-btn" data-type="${type}" data-id="${item.id}">
                            <i class="bi bi-x"></i>
                        </button>
                    `;
                    if (!item.image) {
                        row.querySelector('.quick-saved-thumb').style.visibility = 'hidden';
                    }
                    host.appendChild(row);
                });
            }
        };

        const updateCounts = () => {
            const wishlistCount = getCollection('wishlist').length;
            const compareCount = getCollection('compare').length;
            wishlistCountEls.forEach((el) => { el.textContent = `${wishlistCount}`; });
            compareCountEls.forEach((el) => { el.textContent = `${compareCount}`; });
        };

        const syncButtonStates = () => {
            const wishlistIds = new Set(getCollection('wishlist').map((i) => String(i.id)));
            const compareIds = new Set(getCollection('compare').map((i) => String(i.id)));
            document.querySelectorAll('.wishlist-btn[data-product-id]').forEach((btn) => {
                btn.classList.toggle('is-active', wishlistIds.has(String(btn.dataset.productId)));
            });
            document.querySelectorAll('.compare-btn[data-product-id]').forEach((btn) => {
                btn.classList.toggle('is-active', compareIds.has(String(btn.dataset.productId)));
            });
        };

        const bindStaticButtons = () => {
            document.querySelectorAll('.wishlist-btn[data-product-id]').forEach((btn) => {
                btn.addEventListener('click', async (event) => {
                    event.preventDefault();
                    event.stopPropagation();
                    await toggleCollection('wishlist', btn);
                });
            });
            document.querySelectorAll('.compare-btn[data-product-id]').forEach((btn) => {
                btn.addEventListener('click', async (event) => {
                    event.preventDefault();
                    event.stopPropagation();
                    await toggleCollection('compare', btn);
                });
            });
        };

        document.addEventListener('click', async (event) => {
            const wishlistBtn = event.target.closest('.wishlist-btn');
            if (wishlistBtn) {
                event.preventDefault();
                event.stopPropagation();
                await toggleCollection('wishlist', wishlistBtn);
                return;
            }
            const compareBtn = event.target.closest('.compare-btn');
            if (compareBtn) {
                event.preventDefault();
                event.stopPropagation();
                await toggleCollection('compare', compareBtn);
                return;
            }
            const removeBtn = event.target.closest('.remove-saved-btn');
            if (removeBtn) {
                const type = removeBtn.dataset.type;
                const id = removeBtn.dataset.id;
                if (!type || !id) {
                    return;
                }
                const items = getCollection(type).filter((item) => String(item.id) !== String(id));
                setCollection(type, items);
                renderCollection(type);
                updateCounts();
                syncButtonStates();
            }
        });

        clearWishlistBtn?.addEventListener('click', () => {
            setCollection('wishlist', []);
            renderCollection('wishlist');
            updateCounts();
            syncButtonStates();
            showToast('Wishlist cleared.');
        });

        clearCompareBtn?.addEventListener('click', () => {
            setCollection('compare', []);
            renderCollection('compare');
            updateCounts();
            syncButtonStates();
            showToast('Compare list cleared.');
        });

        if (typeof bootstrap !== 'undefined') {
            const wishlistDrawer = wishlistDrawerEl ? bootstrap.Offcanvas.getOrCreateInstance(wishlistDrawerEl) : null;
            const compareDrawer = compareDrawerEl ? bootstrap.Offcanvas.getOrCreateInstance(compareDrawerEl) : null;
            wishlistToggleBtn?.addEventListener('click', () => wishlistDrawer?.show());
            compareToggleBtn?.addEventListener('click', () => compareDrawer?.show());
        }

        renderCollection('wishlist');
        renderCollection('compare');
        updateCounts();
        const syncWithServer = async () => {
            const config = window.EyetrackConfig || {};
            if (config.isAuthenticated && config.wishlistDataUrl) {
                try {
                    const response = await fetch(config.wishlistDataUrl);
                    const data = await response.json();
                    if (data.ok && data.wishlist) {
                        // Merge or replace local with server? Usually replace for auth users.
                        setCollection('wishlist', data.wishlist);
                        // Also sync counts
                        const wishlistBadges = document.querySelectorAll('[data-wishlist-count]');
                        wishlistBadges.forEach(el => el.textContent = data.wishlist.length);
                    }
                } catch (error) {
                    console.error('Initial wishlist sync failed:', error);
                }
            }
        };

        syncWithServer();
        syncButtonStates();
        updateCounts();
        window.__etsWishlistCompareReady = true;
    };

    const setupCheckoutMicroInteractions = () => {
        const form = document.getElementById('checkoutForm');
        if (!form) {
            return;
        }
        const fields = Array.from(form.querySelectorAll('.checkout-field'));
        const fieldsByName = fields.reduce((map, field) => {
            map[field.name] = field;
            return map;
        }, {});
        const progressBar = document.getElementById('checkoutProgressBar');
        const progressText = document.getElementById('checkoutProgressText');
        const submitBtn = document.getElementById('checkoutSubmitBtn');
        const stepAddress = document.getElementById('checkoutStepAddress');
        const stepPayment = document.getElementById('checkoutStepPayment');
        const savedAddressSelect = document.getElementById('checkoutSavedAddress');

        const validateField = (field) => {
            const value = field.value.trim();
            let valid = value.length > 0;
            if (field.name === 'email') {
                valid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
            }
            if (field.name === 'phone') {
                valid = /^[0-9+ ]{10,15}$/.test(value);
            }
            if (field.name === 'address' || field.name.startsWith('addr_')) {
                valid = value.length >= 2;
                if (field.name === 'addr_pincode') {
                    valid = /^[0-9]{6}$/.test(value);
                }
            }
            field.classList.toggle('is-valid', valid);
            field.classList.toggle('is-invalid', !valid && value.length > 0);
            return valid;
        };

        const initStickyDetailBar = () => {
            const stickyBar = document.querySelector('.sticky-detail-bar');
            const mainActionContainer = document.querySelector('.product-detail-page form[action*="add-to-cart"]');

            if (stickyBar && mainActionContainer) {
                const observer = new IntersectionObserver((entries) => {
                    entries.forEach(entry => {
                        if (!entry.isIntersecting && entry.boundingClientRect.top < 0) {
                            stickyBar.classList.add('visible');
                        } else {
                            stickyBar.classList.remove('visible');
                        }
                    });
                }, { threshold: 0, rootMargin: "-100px 0px 0px 0px" });

                observer.observe(mainActionContainer);
            }
        };

        const refreshProgress = () => {
            const validCount = fields.reduce((count, field) => count + (validateField(field) ? 1 : 0), 0);
            const pct = Math.round((validCount / fields.length) * 100);
            if (progressBar) {
                progressBar.style.width = `${pct}%`;
            }
            if (progressText) {
                progressText.textContent = `Profile completion: ${pct}%`;
            }
            stepAddress?.classList.toggle('done', pct >= 75);
            stepPayment?.classList.toggle('active', pct === 100);
        };

        const applySavedAddressSelection = () => {
            if (!savedAddressSelect) {
                return;
            }

            const selectedOption = savedAddressSelect.options[savedAddressSelect.selectedIndex];
            if (!selectedOption || !selectedOption.value) {
                refreshProgress();
                return;
            }

            const valueMap = {
                full_name: selectedOption.dataset.fullName || '',
                email: selectedOption.dataset.email || '',
                phone: selectedOption.dataset.phone || '',
                addr_house: selectedOption.dataset.house || '',
                addr_landmark: selectedOption.dataset.landmark || '',
                addr_city: selectedOption.dataset.city || '',
                addr_state: selectedOption.dataset.state || '',
                addr_pincode: selectedOption.dataset.pincode || '',
            };

            Object.entries(valueMap).forEach(([name, value]) => {
                const field = fieldsByName[name];
                if (!field) {
                    return;
                }
                field.value = value;
                validateField(field);
            });

            refreshProgress();
        };

        fields.forEach((field) => {
            field.addEventListener('input', refreshProgress);
            field.addEventListener('blur', refreshProgress);
        });

        savedAddressSelect?.addEventListener('change', applySavedAddressSelection);

        form.addEventListener('submit', () => {
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = 'Processing...';
            }
        });

        refreshProgress();
    };

    const setupWishlistPage = (showToast) => {
        const grid = document.getElementById('wishlistPageGrid');
        if (!grid) {
            return;
        }
        const countEls = [
            document.getElementById('wishlistPageCount'),
            document.getElementById('wishlistPageCountMobile'),
        ].filter(Boolean);
        const emptyEl = document.getElementById('wishlistPageEmpty');
        const clearBtns = Array.from(document.querySelectorAll('[data-wishlist-clear]'));
        const csrfToken = getCookie('csrftoken');

        const render = () => {
            const items = getCollection('wishlist');
            grid.innerHTML = '';
            countEls.forEach((el) => { el.textContent = `${items.length}`; });
            if (!items.length) {
                emptyEl?.classList.remove('d-none');
                return;
            }
            emptyEl?.classList.add('d-none');
            items.forEach((item) => {
                const col = document.createElement('div');
                col.className = 'col-md-6 col-xl-4';
                const thumb = item.image || 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw==';
                col.innerHTML = `
                    <article class="wishlist-page-card h-100 d-flex flex-column">
                        <img src="${thumb}" alt="${item.name}" class="wishlist-page-thumb">
                        <div class="p-3 d-flex flex-column flex-grow-1">
                            <h6 class="mb-1"><a href="${item.url}" class="text-decoration-none text-light">${item.name}</a></h6>
                            <p class="product-price mb-3">${item.price ? `Rs ${item.price}` : ''}</p>
                            <div class="d-flex gap-2 mt-auto">
                                <button type="button" class="btn btn-premium-cta btn-sm flex-grow-1 wishlist-add-cart-btn" data-id="${item.id}">Add</button>
                                <details class="mobile-more-actions">
                                    <summary class="btn btn-outline-light btn-sm">More</summary>
                                    <div class="mobile-more-panel">
                                        <a href="${item.url}" class="btn btn-outline-light btn-sm w-100">View</a>
                                        <button type="button" class="btn btn-outline-danger btn-sm w-100 wishlist-remove-btn" data-id="${item.id}">Remove</button>
                                    </div>
                                </details>
                                <button type="button" class="btn btn-outline-danger btn-sm wishlist-remove-btn desktop-secondary-btn" data-id="${item.id}">Remove</button>
                            </div>
                        </div>
                    </article>
                `;
                grid.appendChild(col);
            });
        };

        grid.addEventListener('click', async (event) => {
            const removeBtn = event.target.closest('.wishlist-remove-btn');
            if (removeBtn) {
                const id = removeBtn.dataset.id;
                const next = getCollection('wishlist').filter((item) => String(item.id) !== String(id));
                setCollection('wishlist', next);
                showToast('Removed from wishlist.');
                render();
                return;
            }
            const addBtn = event.target.closest('.wishlist-add-cart-btn');
            if (addBtn) {
                const id = addBtn.dataset.id;
                if (!id) {
                    return;
                }
                try {
                    const response = await fetch(`/add-to-cart/${id}/`, {
                        method: 'POST',
                        headers: {
                            'X-Requested-With': 'XMLHttpRequest',
                            'Accept': 'application/json',
                            'X-CSRFToken': csrfToken,
                            'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
                        },
                        body: `next=${encodeURIComponent(window.location.pathname)}`,
                    });
                    const data = await response.json();
                    if (!response.ok || !data.ok) {
                        showToast(data.message || 'Unable to add item.', 'error');
                        return;
                    }
                    showToast(data.message || 'Item added to cart.');
                    const cartBadges = document.querySelectorAll('[data-cart-count]');
                    cartBadges.forEach((badge) => {
                        badge.textContent = `${data.cart_count || badge.textContent}`;
                    });
                } catch (error) {
                    showToast('Network error. Please retry.', 'error');
                }
            }
        });

        clearBtns.forEach((btn) => {
            btn.addEventListener('click', () => {
                setCollection('wishlist', []);
                showToast('Wishlist cleared.');
                render();
            });
        });

        render();
    };

    const setupComparePage = (showToast) => {
        const tbody = document.getElementById('comparePageBody');
        if (!tbody) {
            return;
        }
        const countEls = [
            document.getElementById('comparePageCount'),
            document.getElementById('comparePageCountMobile'),
        ].filter(Boolean);
        const emptyEl = document.getElementById('comparePageEmpty');
        const clearBtns = Array.from(document.querySelectorAll('[data-compare-clear]'));
        const shareBtns = Array.from(document.querySelectorAll('[data-compare-share]'));
        const exportBtns = Array.from(document.querySelectorAll('[data-compare-export]'));
        const syncFromQuery = () => {
            const idsParam = new URLSearchParams(window.location.search).get('ids');
            if (!idsParam) {
                return;
            }
            const parsedIds = idsParam
                .split(',')
                .map((id) => id.trim())
                .filter((id) => /^\d+$/.test(id))
                .slice(0, 4)
                .map((id) => ({ id }));
            if (!parsedIds.length) {
                return;
            }
            const current = getCollection('compare');
            if (!current.length) {
                setCollection('compare', parsedIds);
            }
        };
        syncFromQuery();

        const fetchProduct = async (id) => {
            try {
                const response = await fetch(`/api/product/${id}/quick-view/`, { headers: { 'Accept': 'application/json' } });
                if (!response.ok) {
                    return null;
                }
                const data = await response.json();
                return data.ok ? data.product : null;
            } catch {
                return null;
            }
        };

        const toNumber = (value) => {
            const num = Number.parseFloat(String(value || '').replace(/[^0-9.]/g, ''));
            return Number.isFinite(num) ? num : 0;
        };
        const compareShell = document.getElementById('comparePageTable');
        const getSpec = (item, key) => (item.specs && item.specs[key] ? item.specs[key] : '-');
        const yesNoClass = (value) => (String(value).toLowerCase() === 'yes' ? 'compare-check yes' : 'compare-check no');
        const yesNoIcon = (value) => (String(value).toLowerCase() === 'yes' ? '✔ Yes' : '✖ No');
        const numberFromSpec = (item, key) => toNumber(getSpec(item, key));
        const dataCell = (content, className = '') => `<div class="compare-data-cell${className ? ` ${className}` : ''}">${content}</div>`;

        const getStockBadgeClass = (stock) => {
            if (stock === 0) return 'compare-stock-badge out-of-stock';
            if (stock < 5) return 'compare-stock-badge low-stock';
            return 'compare-stock-badge in-stock';
        };

        const getStockBadgeText = (stock) => {
            if (stock === 0) return 'Out of Stock';
            if (stock < 5) return `${stock} Left`;
            return 'In Stock';
        };

        const render = async () => {
            const storedItems = getCollection('compare');
            countEls.forEach((el) => { el.textContent = `${storedItems.length}`; });
            if (!storedItems.length) {
                tbody.innerHTML = '';
                compareShell?.style.setProperty('--compare-cols', '1');
                emptyEl?.classList.remove('d-none');
                return;
            }
            emptyEl?.classList.add('d-none');
            tbody.style.opacity = '0.5';
            tbody.style.pointerEvents = 'none';

            // Validate all products are from same category
            const categories = new Set(storedItems.map(item => item.category).filter(Boolean));
            if (categories.size > 1) {
                tbody.innerHTML = `
                    <div class="compare-grid-message">
                        <div class="display-6 mb-2 text-danger"><i class="bi bi-exclamation-triangle"></i></div>
                        <h5 class="mb-2">Invalid Comparison</h5>
                        <p class="text-secondary mb-3">Products must be from the same category to compare.</p>
                        <p class="small text-secondary">Categories found: ${Array.from(categories).join(', ')}</p>
                    </div>
                `;
                compareShell?.style.setProperty('--compare-cols', '1');
                tbody.style.opacity = '';
                tbody.style.pointerEvents = '';
                return;
            }

            const liveItems = await Promise.all(storedItems.map(async (item) => {
                const live = await fetchProduct(item.id);
                return live ? { ...item, ...live } : item;
            }));
            const compareCols = Math.max(liveItems.length, 1);
            const compareGridTemplate = `220px repeat(${compareCols}, minmax(0, 1fr))`;
            compareShell?.style.setProperty('--compare-cols', String(compareCols));

            const prices = liveItems.map((item) => toNumber(item.price)).filter((v) => v > 0);
            const bestPrice = prices.length ? Math.min(...prices) : 0;
            const stocks = liveItems.map((item) => Number(item.stock) || 0);
            const bestStock = stocks.length ? Math.max(...stocks) : 0;
            const bestResolution = Math.max(...liveItems.map((item) => numberFromSpec(item, 'resolution_mp')));
            const bestNightVision = Math.max(...liveItems.map((item) => numberFromSpec(item, 'night_vision_range_m')));
            const bestFov = Math.max(...liveItems.map((item) => numberFromSpec(item, 'field_of_view_deg')));
            const bestWarranty = Math.max(...liveItems.map((item) => numberFromSpec(item, 'warranty_years')));

            const productCells = liveItems.map((item) => {
                const itemPrice = toNumber(item.price);
                const stock = Number(item.stock) || 0;
                const bestPriceBadge = bestPrice > 0 && itemPrice === bestPrice
                    ? `<span class="compare-chip best-price">Best Price</span>` : '';
                const bestStockBadge = bestStock > 0 && stock === bestStock
                    ? `<span class="compare-chip best-stock">Top Stock</span>` : '';
                const image = item.image
                    ? `<img src="${item.image}" alt="${item.name || 'Product'}" class="compare-product-image">`
                    : `<div class="compare-product-image-placeholder"><i class="bi bi-camera-video"></i></div>`;

                return `
                    <td class="compare-data-cell">
                        <div class="compare-product-header">
                            ${image}
                            <h6 class="compare-product-name">${item.name || '-'}</h6>
                            <p class="compare-product-price">${item.price ? `₹${item.price}` : '-'}</p>
                            <div class="d-flex gap-2 flex-wrap justify-content-center mb-2">
                                ${bestPriceBadge}${bestStockBadge}
                            </div>
                            <div class="compare-product-actions">
                                <a class="btn btn-sm compare-view-product d-inline-flex align-items-center justify-content-center gap-1" href="${item.url || item.product_url || '#'}"><i class="bi bi-eye"></i>View</a>
                                <button class="btn btn-sm compare-remove-product d-inline-flex align-items-center justify-content-center gap-1 compare-remove-page-btn" data-id="${item.id}"><i class="bi bi-trash3"></i>Remove</button>
                            </div>
                        </div>
                    </td>
                `;
            }).join('');

            // Determine category and create appropriate spec rows
            const category = categories.values().next().value;

            let specRows = [];

            if (category === 'CCTV Cameras') {
                specRows = [
                    {
                        label: 'Camera Type',
                        value: liveItems.map((item) => `<td class="compare-data-cell">${getSpec(item, 'camera_type')}</td>`).join(''),
                        className: ''
                    },
                    {
                        label: 'Resolution',
                        value: liveItems.map((item) => {
                            const value = getSpec(item, 'resolution_mp');
                            const best = bestResolution > 0 && numberFromSpec(item, 'resolution_mp') === bestResolution;
                            return `<td class="compare-data-cell ${best ? 'compare-best' : ''}">${value}</td>`;
                        }).join(''),
                        className: ''
                    },
                    {
                        label: 'Night Vision Range',
                        value: liveItems.map((item) => {
                            const value = getSpec(item, 'night_vision_range_m');
                            const best = bestNightVision > 0 && numberFromSpec(item, 'night_vision_range_m') === bestNightVision;
                            return `<td class="compare-data-cell ${best ? 'compare-best' : ''}">${value}</td>`;
                        }).join(''),
                        className: ''
                    },
                    {
                        label: 'Field of View',
                        value: liveItems.map((item) => {
                            const value = getSpec(item, 'field_of_view_deg');
                            const best = bestFov > 0 && numberFromSpec(item, 'field_of_view_deg') === bestFov;
                            return `<td class="compare-data-cell ${best ? 'compare-best' : ''}">${value}</td>`;
                        }).join(''),
                        className: ''
                    },
                    {
                        label: 'Lens',
                        value: liveItems.map((item) => `<td class="compare-data-cell">${getSpec(item, 'lens')}</td>`).join(''),
                        className: ''
                    },
                    {
                        label: 'Frame Rate',
                        value: liveItems.map((item) => `<td class="compare-data-cell">${getSpec(item, 'frame_rate')}</td>`).join(''),
                        className: ''
                    },
                    {
                        label: 'Weatherproof',
                        value: liveItems.map((item) => `<td class="compare-data-cell">${getSpec(item, 'weatherproof')}</td>`).join(''),
                        className: ''
                    },
                    {
                        label: 'Connectivity',
                        value: liveItems.map((item) => `<td class="compare-data-cell">${getSpec(item, 'connectivity')}</td>`).join(''),
                        className: ''
                    },
                    {
                        label: 'Power Source',
                        value: liveItems.map((item) => `<td class="compare-data-cell">${getSpec(item, 'power_source')}</td>`).join(''),
                        className: ''
                    },
                    {
                        label: 'Storage Support',
                        value: liveItems.map((item) => `<td class="compare-data-cell">${getSpec(item, 'storage_support')}</td>`).join(''),
                        className: ''
                    },
                    {
                        label: 'Audio Support',
                        value: liveItems.map((item) => {
                            const val = getSpec(item, 'audio_support');
                            return `<td class="compare-data-cell"><span class="${yesNoClass(val)}">${yesNoIcon(val)}</span></td>`;
                        }).join(''),
                        className: ''
                    },
                    {
                        label: 'AI Detection',
                        value: liveItems.map((item) => {
                            const val = getSpec(item, 'ai_detection');
                            return `<td class="compare-data-cell"><span class="${yesNoClass(val)}">${yesNoIcon(val)}</span></td>`;
                        }).join(''),
                        className: ''
                    },
                    {
                        label: 'Warranty',
                        value: liveItems.map((item) => {
                            const value = getSpec(item, 'warranty_years');
                            const best = bestWarranty > 0 && numberFromSpec(item, 'warranty_years') === bestWarranty;
                            return `<td class="compare-data-cell ${best ? 'compare-best' : ''}">${value}</td>`;
                        }).join(''),
                        className: ''
                    },
                ];
            } else if (category === 'Video Door Phones') {
                specRows = [
                    {
                        label: 'Screen Size',
                        value: liveItems.map((item) => `<td class="compare-data-cell">${getSpec(item, 'screen_size')}</td>`).join(''),
                        className: ''
                    },
                    {
                        label: 'Camera Resolution',
                        value: liveItems.map((item) => `<td class="compare-data-cell">${getSpec(item, 'camera_resolution')}</td>`).join(''),
                        className: ''
                    },
                    {
                        label: 'Night Vision',
                        value: liveItems.map((item) => {
                            const val = getSpec(item, 'night_vision');
                            return `<td class="compare-data-cell"><span class="${yesNoClass(val)}">${yesNoIcon(val)}</span></td>`;
                        }).join(''),
                        className: ''
                    },
                    {
                        label: 'Connectivity Type',
                        value: liveItems.map((item) => `<td class="compare-data-cell">${getSpec(item, 'connectivity_type')}</td>`).join(''),
                        className: ''
                    },
                    {
                        label: 'Unlock Method',
                        value: liveItems.map((item) => `<td class="compare-data-cell">${getSpec(item, 'unlock_method')}</td>`).join(''),
                        className: ''
                    },
                    {
                        label: 'Audio Communication',
                        value: liveItems.map((item) => {
                            const val = getSpec(item, 'audio_communication');
                            return `<td class="compare-data-cell"><span class="${yesNoClass(val)}">${yesNoIcon(val)}</span></td>`;
                        }).join(''),
                        className: ''
                    },
                    {
                        label: 'Mobile App Support',
                        value: liveItems.map((item) => {
                            const val = getSpec(item, 'mobile_app_support');
                            return `<td class="compare-data-cell"><span class="${yesNoClass(val)}">${yesNoIcon(val)}</span></td>`;
                        }).join(''),
                        className: ''
                    },
                    {
                        label: 'Storage Support',
                        value: liveItems.map((item) => `<td class="compare-data-cell">${getSpec(item, 'storage_support')}</td>`).join(''),
                        className: ''
                    },
                    {
                        label: 'Power Source',
                        value: liveItems.map((item) => `<td class="compare-data-cell">${getSpec(item, 'power_source')}</td>`).join(''),
                        className: ''
                    },
                    {
                        label: 'Installation Type',
                        value: liveItems.map((item) => `<td class="compare-data-cell">${getSpec(item, 'installation_type')}</td>`).join(''),
                        className: ''
                    },
                    {
                        label: 'Warranty',
                        value: liveItems.map((item) => `<td class="compare-data-cell">${getSpec(item, 'warranty')}</td>`).join(''),
                        className: ''
                    },
                ];
            }

            const rows = [
                {
                    label: 'Product',
                    value: productCells,
                    className: ''
                },
                {
                    label: 'Category',
                    value: liveItems.map((item) => `<td class="compare-data-cell">${item.category || '-'}</td>`).join(''),
                    className: ''
                },
                ...specRows,
                {
                    label: 'Description',
                    value: liveItems.map((item) => `<td class="compare-data-cell">${(item.description || '-').toString().slice(0, 140)}</td>`).join(''),
                    className: ''
                },
            ];

            tbody.innerHTML = rows.map((row) => `
                <div class="compare-grid-row ${row.className}" style="grid-template-columns: ${compareGridTemplate};">
                    <div class="compare-attribute-name">${row.label}</div>
                    ${row.value}
                </div>
            `).join('')
                .replaceAll('<td class="compare-data-cell">', '<div class="compare-data-cell">')
                .replace(/<td class="compare-data-cell ([^"]+)">/g, '<div class="compare-data-cell $1">')
                .replaceAll('</td>', '</div>');
            tbody.style.opacity = '';
            tbody.style.pointerEvents = '';

            const categoryNoteEl = document.getElementById('compareCategoryNote');
            if (category && liveItems.length > 0) {
                categoryNoteEl.style.display = 'block';
                categoryNoteEl.innerHTML = `<i class="bi bi-info-circle me-1"></i> Showing specifications for <strong>${category}</strong>. Highlighted cells mark the best value.`;
            } else {
                categoryNoteEl.style.display = 'none';
            }
        };

        tbody.addEventListener('click', (event) => {
            const removeBtn = event.target.closest('.compare-remove-page-btn');
            if (!removeBtn) {
                return;
            }
            const id = removeBtn.dataset.id;
            const next = getCollection('compare').filter((item) => String(item.id) !== String(id));
            setCollection('compare', next);
            showToast('Removed from compare list.');
            render();
        });

        const onShareClick = async () => {
            const ids = getCollection('compare').map((item) => item.id).filter(Boolean).slice(0, 4);
            if (!ids.length) {
                showToast('Add items before sharing compare link.', 'error');
                return;
            }
            const url = `${window.location.origin}${window.location.pathname}?ids=${ids.join(',')}`;
            try {
                if (navigator.clipboard?.writeText) {
                    await navigator.clipboard.writeText(url);
                } else {
                    const helper = document.createElement('textarea');
                    helper.value = url;
                    document.body.appendChild(helper);
                    helper.select();
                    document.execCommand('copy');
                    helper.remove();
                }
                showToast('Compare link copied to clipboard.');
            } catch (error) {
                showToast('Unable to copy link. Please copy manually.', 'error');
            }
        };

        const onExportClick = () => {
            const compareCount = getCollection('compare').length;
            if (!compareCount) {
                showToast('Nothing to export. Add compare items first.', 'error');
                return;
            }
            document.body.classList.add('print-compare');
            window.print();
            window.setTimeout(() => {
                document.body.classList.remove('print-compare');
            }, 280);
            showToast('Print dialog opened for PDF export.');
        };

        clearBtns.forEach((btn) => {
            btn.addEventListener('click', () => {
                setCollection('compare', []);
                showToast('Compare list cleared.');
                render();
            });
        });

        shareBtns.forEach((btn) => btn.addEventListener('click', onShareClick));
        exportBtns.forEach((btn) => btn.addEventListener('click', onExportClick));

        render();
    };

    const setupSkeletonLoading = () => {
        const path = window.location.pathname;
        const skeletonTargets = [];

        if (path.includes('/cart/')) {
            skeletonTargets.push(...document.querySelectorAll('.premium-table tbody tr, .summary-line, .compact-product'));
        }
        if (path.includes('/checkout/')) {
            skeletonTargets.push(...document.querySelectorAll('.compact-row, .summary-line, .checkout-step'));
        }
        if (path === '/' || path.includes('/category/') || path.includes('/product/') || path.endsWith('/store/') || path.includes('/product/')) {
            skeletonTargets.push(...document.querySelectorAll('.product-card, .mini-info-card, .compact-row, .compact-product'));
        }

        const uniqueTargets = Array.from(new Set(skeletonTargets)).slice(0, 18);
        if (!uniqueTargets.length || prefersReducedMotion) {
            return;
        }

        root.classList.add('has-skeleton');
        uniqueTargets.forEach((el) => el.classList.add('skeleton-on-load'));

        const hydrate = () => {
            root.classList.add('is-hydrated');
            window.setTimeout(() => {
                root.classList.remove('has-skeleton');
                uniqueTargets.forEach((el) => el.classList.remove('skeleton-on-load'));
            }, 260);
        };

        window.setTimeout(hydrate, 540);
    };

    const setupAjaxCatalog = () => {
        const gridCol = document.getElementById('catalogGridCol');
        if (!gridCol) return;

        const updateCatalog = async (url) => {
            gridCol.style.opacity = '0.4';
            gridCol.style.pointerEvents = 'none';

            try {
                const response = await fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
                if (!response.ok) throw new Error('Bad response');
                
                const htmlString = await response.text();
                const parser = new DOMParser();
                const doc = parser.parseFromString(htmlString, 'text/html');

                const newGridCol = doc.getElementById('catalogGridCol');
                if (newGridCol) {
                    gridCol.innerHTML = newGridCol.innerHTML;
                    window.history.pushState({}, '', url);
                    
                    const newForm = doc.getElementById('catalogFilterForm');
                    const currentForm = document.getElementById('catalogFilterForm');
                    if (newForm && currentForm) {
                        currentForm.innerHTML = newForm.innerHTML;
                    }

                    const newDockCount = doc.getElementById('mobileFilterCountDock');
                    const currentDockCount = document.getElementById('mobileFilterCountDock');
                    if (newDockCount && currentDockCount) {
                        currentDockCount.textContent = newDockCount.textContent;
                        currentDockCount.style.opacity = newDockCount.style.opacity;
                    }

                    if (typeof setupCardTilt === 'function') setupCardTilt();
                    
                    // Re-trigger badge count
                    const inputEvent = new Event('input', { bubbles: true });
                    currentForm.dispatchEvent(inputEvent);
                }
            } catch (err) {
                window.location.href = url;
            } finally {
                gridCol.style.opacity = '1';
                gridCol.style.pointerEvents = 'all';
                const catalogSection = document.getElementById('catalog');
                if (catalogSection) {
                    const offsetPosition = catalogSection.getBoundingClientRect().top + window.scrollY - 80;
                    window.scrollTo({ top: offsetPosition, behavior: 'smooth' });
                }
            }
        };

        document.addEventListener('click', (e) => {
            const link = e.target.closest('#catalogGridCol .pagination a.page-link, #catalogGridCol .active-filter-clear, #mobileFilters .filter-reset-link');
            if (link && link.href && !link.href.includes('#')) {
                e.preventDefault();
                updateCatalog(link.href);
            }
        });

        document.addEventListener('submit', (e) => {
            const form = e.target.closest('#catalogFilterForm');
            if (form) {
                e.preventDefault();
                const url = new URL(form.action || window.location.href);
                const formData = new FormData(form);
                const searchParams = new URLSearchParams();
                for (const [key, value] of formData.entries()) {
                    if (value.trim() !== '') {
                        searchParams.append(key, value);
                    }
                }
                url.search = searchParams.toString();
                updateCatalog(url.toString());
            }
        });

        window.addEventListener('popstate', () => {
            if (window.location.pathname.includes('/store/') || window.location.pathname.includes('/category/') || window.location.pathname === '/' || window.location.pathname === '/products/') {
                updateCatalog(window.location.href);
            }
        });
    };

    const init = () => {
        const showToast = setupPremiumToast();
        markReady();
        setupSkeletonLoading();
        setupPageTransitionHooks();
        setupCatalogFiltersLayout();
        setupMobileFilterUx();
        setupProductCardNavigation();
        setupSmartScrollUI();
        setupAnchorScrolling();
        setupCardTilt();
        setupQuickCartDrawer(showToast);
        setupQuickView();
        setupWishlistCompare(showToast);
        setupCheckoutMicroInteractions();
        if (typeof setupWishlistPage !== 'undefined') setupWishlistPage(showToast);
        if (typeof setupComparePage !== 'undefined') setupComparePage(showToast);
        setupAjaxCatalog();
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init, { once: true });
    } else {
        init();
    }

})();

/* Product Detail Gallery Switching */
document.addEventListener('DOMContentLoaded', function() {
    const mainImage = document.getElementById('main-detail-image');
    const thumbnails = document.querySelectorAll('.thumbnail-item');

    if (mainImage && thumbnails.length > 0) {
        thumbnails.forEach(thumb => {
            thumb.addEventListener('click', function() {
                const newSrc = this.dataset.src;
                
                // Reset active state for all thumbnails
                thumbnails.forEach(t => t.classList.remove('active'));
                // Set active state for clicked thumbnail
                this.classList.add('active');
                
                // Apply fade out effect
                mainImage.style.opacity = '0';
                
                setTimeout(() => {
                    mainImage.src = newSrc;
                    mainImage.style.opacity = '1';
                }, 300);
            });
        });
    }
});

/* Notifications Logic */
document.addEventListener('DOMContentLoaded', function() {
    const notificationDrawer = document.getElementById('notificationDrawer');
    const badge = document.getElementById('globalUnreadBadge');
    const drawerBody = document.getElementById('notificationDrawerBody');
    const markAllReadBtn = document.getElementById('markAllReadBtn');
    
    if(!notificationDrawer) return;

    function fetchNotifications() {
        fetch('/accounts/api/notifications/')
            .then(res => res.json())
            .then(data => {
                const unreadCount = data.unread_count;
                if (unreadCount > 0) {
                    badge.textContent = unreadCount > 9 ? '9+' : unreadCount;
                    badge.classList.remove('d-none');
                } else {
                    badge.classList.add('d-none');
                }
                drawerBody.innerHTML = data.html;
                attachNotificationListeners();
            })
            .catch(err => console.error("Error fetching notifications", err));
    }

    function attachNotificationListeners() {
        // We now use event delegation on drawerBody for better reliability
        if (!drawerBody.dataset.listenerAttached) {
            drawerBody.addEventListener('click', function(e) {
                const item = e.target.closest('.notification-item');
                if (!item) return;
                
                // Prevent modal if user clicked a specific action button inside
                if (e.target.closest('.notification-action-btn')) return;

                console.log("Notification item clicked:", item.dataset.id);

                const notificationId = item.dataset.id;
                const title = item.dataset.title || 'Notification';
                const message = item.dataset.message || '';
                const link = item.dataset.link;
                const type = item.dataset.type;

                // Mark as read immediately
                if (item.classList.contains('is-unread')) {
                    fetch(`/accounts/api/notifications/${notificationId}/read/`, { 
                        method: 'POST', 
                        headers: { 
                            'X-CSRFToken': window.EyetrackConfig?.csrfToken,
                            'Content-Type': 'application/json'
                        } 
                    }).then(() => {
                        item.classList.remove('is-unread');
                        const dot = item.querySelector('.unread-dot');
                        if (dot) dot.remove();
                        if (badge) {
                            let current = parseInt(badge.textContent);
                            if (!isNaN(current)) {
                                current--;
                                if (current <= 0) badge.classList.add('d-none');
                                else badge.textContent = current;
                            } else if (badge.textContent === '9+') {
                                fetchNotifications();
                            }
                        }
                    });
                }

                // Show detailed modal
                let icon = 'info';
                if (type === 'order') icon = 'success';
                else if (type === 'offer') icon = 'info';
                else if (type === 'alert') icon = 'warning';

                if (window.Swal) {
                    Swal.fire({
                        title: title,
                        text: message,
                        icon: icon,
                        showCancelButton: !!link,
                        confirmButtonText: link ? 'Close' : 'OK',
                        cancelButtonText: 'View Details',
                        buttonsStyling: false,
                        customClass: {
                            popup: 'swal-glass-popup',
                            title: 'swal-glass-title',
                            confirmButton: 'swal-btn-cancel btn me-2',
                            cancelButton: 'swal-btn-confirm btn'
                        }
                    }).then((result) => {
                        if (result.isDismissed && result.dismiss === Swal.DismissReason.cancel && link) {
                            window.location.href = link;
                        }
                    });
                } else {
                    alert(title + "\n\n" + message);
                }
            });
            drawerBody.dataset.listenerAttached = "true";
        }
    }

    notificationDrawer.addEventListener('show.bs.offcanvas', fetchNotifications);

    if (markAllReadBtn) {
        markAllReadBtn.addEventListener('click', function() {
            fetch('/accounts/api/notifications/clear/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': window.EyetrackConfig?.csrfToken
                }
            }).then(() => fetchNotifications());
        });
    }

    // Initial fetch to show unread dot
    if (window.EyetrackConfig && window.EyetrackConfig.isAuthenticated) {
        fetchNotifications();
    }
});
