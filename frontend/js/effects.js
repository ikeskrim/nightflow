/**
 * NightFlow Effects Library
 * Premium interactive effects for high-end user experiences
 * Version: 1.0.0
 */

(function () {
  'use strict';

  // ============================================================================
  // CONFIGURATION
  // ============================================================================

  const CONFIG = {
    cursor: {
      enabled: true,
      lerp: 0.15, // Smoothing factor for cursor movement
      ringLerp: 0.08, // Slower smoothing for ring
      hoverScale: 1.5,
      clickScale: 0.8,
    },
    magnetic: {
      enabled: true,
      strength: 0.3, // How strongly elements pull toward cursor
      threshold: 100, // Distance threshold in pixels
      returnSpeed: 0.3, // Speed of return animation
    },
    scroll: {
      threshold: 0.1, // IntersectionObserver threshold
      rootMargin: '0px 0px -50px 0px',
    },
    stagger: {
      baseDelay: 100, // Base delay between staggered items in ms
    },
    smoothScroll: {
      duration: 800,
      easing: 'easeOutExpo',
    },
  };

  // ============================================================================
  // UTILITY FUNCTIONS
  // ============================================================================

  /**
   * Linear interpolation between two values
   */
  function lerp(start, end, factor) {
    return start + (end - start) * factor;
  }

  /**
   * Clamp a value between min and max
   */
  function clamp(value, min, max) {
    return Math.min(Math.max(value, min), max);
  }

  /**
   * Calculate distance between two points
   */
  function distance(x1, y1, x2, y2) {
    return Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2));
  }

  /**
   * Map a value from one range to another
   */
  function mapRange(value, inMin, inMax, outMin, outMax) {
    return ((value - inMin) * (outMax - outMin)) / (inMax - inMin) + outMin;
  }

  /**
   * Easing functions
   */
  const Easing = {
    linear: (t) => t,
    easeInQuad: (t) => t * t,
    easeOutQuad: (t) => t * (2 - t),
    easeInOutQuad: (t) => (t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t),
    easeInCubic: (t) => t * t * t,
    easeOutCubic: (t) => --t * t * t + 1,
    easeInOutCubic: (t) =>
      t < 0.5 ? 4 * t * t * t : (t - 1) * (2 * t - 2) * (2 * t - 2) + 1,
    easeOutExpo: (t) => (t === 1 ? 1 : 1 - Math.pow(2, -10 * t)),
    easeOutBack: (t) => {
      const c1 = 1.70158;
      const c3 = c1 + 1;
      return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2);
    },
  };

  /**
   * Check if device supports hover (not touch-only)
   */
  function supportsHover() {
    return window.matchMedia('(hover: hover)').matches;
  }

  /**
   * Check if user prefers reduced motion
   */
  function prefersReducedMotion() {
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }

  /**
   * Debounce function
   */
  function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }

  /**
   * Throttle function
   */
  function throttle(func, limit) {
    let inThrottle;
    return function (...args) {
      if (!inThrottle) {
        func.apply(this, args);
        inThrottle = true;
        setTimeout(() => (inThrottle = false), limit);
      }
    };
  }

  // ============================================================================
  // 1. CUSTOM CURSOR TRACKING
  // ============================================================================

  class CustomCursor {
    constructor() {
      if (!supportsHover() || prefersReducedMotion()) {
        return;
      }

      this.cursor = null;
      this.ring = null;
      this.position = { x: 0, y: 0 };
      this.targetPosition = { x: 0, y: 0 };
      this.ringPosition = { x: 0, y: 0 };
      this.isHovering = false;
      this.isClicking = false;
      this.isVisible = false;
      this.rafId = null;

      this.init();
    }

    init() {
      // Create cursor elements
      this.cursor = document.createElement('div');
      this.cursor.className = 'custom-cursor';
      this.cursor.style.opacity = '0';

      this.ring = document.createElement('div');
      this.ring.className = 'custom-cursor-ring';
      this.ring.style.opacity = '0';

      document.body.appendChild(this.cursor);
      document.body.appendChild(this.ring);

      // Bind event listeners
      this.bindEvents();

      // Start animation loop
      this.animate();
    }

    bindEvents() {
      // Mouse move
      document.addEventListener('mousemove', (e) => {
        this.targetPosition.x = e.clientX;
        this.targetPosition.y = e.clientY;

        if (!this.isVisible) {
          this.isVisible = true;
          this.position.x = e.clientX;
          this.position.y = e.clientY;
          this.ringPosition.x = e.clientX;
          this.ringPosition.y = e.clientY;
          this.cursor.style.opacity = '1';
          this.ring.style.opacity = '1';
        }
      });

      // Mouse leave window
      document.addEventListener('mouseleave', () => {
        this.isVisible = false;
        this.cursor.style.opacity = '0';
        this.ring.style.opacity = '0';
      });

      // Mouse enter window
      document.addEventListener('mouseenter', () => {
        this.isVisible = true;
        this.cursor.style.opacity = '1';
        this.ring.style.opacity = '1';
      });

      // Mouse down
      document.addEventListener('mousedown', () => {
        this.isClicking = true;
        this.cursor.classList.add('cursor-click');
        this.ring.classList.add('cursor-click');
      });

      // Mouse up
      document.addEventListener('mouseup', () => {
        this.isClicking = false;
        this.cursor.classList.remove('cursor-click');
        this.ring.classList.remove('cursor-click');
      });

      // Hover effects on interactive elements
      const hoverTargets = document.querySelectorAll(
        'a, button, [role="button"], input, textarea, select, .cursor-hover, [data-cursor="hover"]'
      );

      hoverTargets.forEach((target) => {
        target.addEventListener('mouseenter', () => this.setHover(true));
        target.addEventListener('mouseleave', () => this.setHover(false));
      });

      // Use MutationObserver to handle dynamically added elements
      const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
          mutation.addedNodes.forEach((node) => {
            if (node.nodeType === 1) {
              const targets = node.querySelectorAll
                ? node.querySelectorAll(
                    'a, button, [role="button"], input, textarea, select, .cursor-hover, [data-cursor="hover"]'
                  )
                : [];
              targets.forEach((target) => {
                target.addEventListener('mouseenter', () => this.setHover(true));
                target.addEventListener('mouseleave', () => this.setHover(false));
              });
              // Check if the node itself is a target
              if (
                node.matches &&
                node.matches(
                  'a, button, [role="button"], input, textarea, select, .cursor-hover, [data-cursor="hover"]'
                )
              ) {
                node.addEventListener('mouseenter', () => this.setHover(true));
                node.addEventListener('mouseleave', () => this.setHover(false));
              }
            }
          });
        });
      });

      observer.observe(document.body, { childList: true, subtree: true });
    }

    setHover(isHovering) {
      this.isHovering = isHovering;
      if (isHovering) {
        this.cursor.classList.add('cursor-hover');
        this.ring.classList.add('cursor-hover');
      } else {
        this.cursor.classList.remove('cursor-hover');
        this.ring.classList.remove('cursor-hover');
      }
    }

    animate() {
      // Smooth cursor movement with lerp
      this.position.x = lerp(
        this.position.x,
        this.targetPosition.x,
        CONFIG.cursor.lerp
      );
      this.position.y = lerp(
        this.position.y,
        this.targetPosition.y,
        CONFIG.cursor.lerp
      );

      // Ring follows with more lag
      this.ringPosition.x = lerp(
        this.ringPosition.x,
        this.targetPosition.x,
        CONFIG.cursor.ringLerp
      );
      this.ringPosition.y = lerp(
        this.ringPosition.y,
        this.targetPosition.y,
        CONFIG.cursor.ringLerp
      );

      // Apply transforms
      this.cursor.style.left = `${this.position.x}px`;
      this.cursor.style.top = `${this.position.y}px`;
      this.ring.style.left = `${this.ringPosition.x}px`;
      this.ring.style.top = `${this.ringPosition.y}px`;

      this.rafId = requestAnimationFrame(() => this.animate());
    }

    destroy() {
      if (this.rafId) {
        cancelAnimationFrame(this.rafId);
      }
      if (this.cursor) this.cursor.remove();
      if (this.ring) this.ring.remove();
    }
  }

  // ============================================================================
  // 2. MAGNETIC BUTTON EFFECT
  // ============================================================================

  class MagneticElement {
    constructor(element) {
      this.element = element;
      this.boundingRect = null;
      this.centerX = 0;
      this.centerY = 0;
      this.isHovering = false;
      this.currentX = 0;
      this.currentY = 0;
      this.targetX = 0;
      this.targetY = 0;
      this.rafId = null;

      this.strength =
        parseFloat(element.dataset.magneticStrength) || CONFIG.magnetic.strength;
      this.threshold =
        parseFloat(element.dataset.magneticThreshold) || CONFIG.magnetic.threshold;

      if (!prefersReducedMotion()) {
        this.init();
      }
    }

    init() {
      this.calculateBounds();
      this.bindEvents();
      this.animate();
    }

    calculateBounds() {
      this.boundingRect = this.element.getBoundingClientRect();
      this.centerX = this.boundingRect.left + this.boundingRect.width / 2;
      this.centerY = this.boundingRect.top + this.boundingRect.height / 2;
    }

    bindEvents() {
      this.element.addEventListener('mouseenter', () => {
        this.isHovering = true;
        this.calculateBounds();
      });

      this.element.addEventListener('mouseleave', () => {
        this.isHovering = false;
        this.targetX = 0;
        this.targetY = 0;
      });

      this.element.addEventListener('mousemove', (e) => {
        if (!this.isHovering) return;

        const dist = distance(e.clientX, e.clientY, this.centerX, this.centerY);

        if (dist < this.threshold) {
          const power = mapRange(dist, 0, this.threshold, 1, 0);
          this.targetX = (e.clientX - this.centerX) * power * this.strength;
          this.targetY = (e.clientY - this.centerY) * power * this.strength;
        } else {
          this.targetX = 0;
          this.targetY = 0;
        }
      });

      // Recalculate on scroll and resize
      window.addEventListener(
        'scroll',
        debounce(() => this.calculateBounds(), 100),
        { passive: true }
      );

      window.addEventListener(
        'resize',
        debounce(() => this.calculateBounds(), 100)
      );
    }

    animate() {
      // Smooth interpolation
      this.currentX = lerp(this.currentX, this.targetX, CONFIG.magnetic.returnSpeed);
      this.currentY = lerp(this.currentY, this.targetY, CONFIG.magnetic.returnSpeed);

      // Apply transform
      this.element.style.transform = `translate(${this.currentX}px, ${this.currentY}px)`;

      this.rafId = requestAnimationFrame(() => this.animate());
    }

    destroy() {
      if (this.rafId) {
        cancelAnimationFrame(this.rafId);
      }
      this.element.style.transform = '';
    }
  }

  /**
   * Initialize magnetic effect on elements
   */
  function initMagneticElements() {
    if (!CONFIG.magnetic.enabled || prefersReducedMotion()) return;

    const elements = document.querySelectorAll('[data-magnetic], .magnetic');
    const instances = [];

    elements.forEach((el) => {
      instances.push(new MagneticElement(el));
    });

    return instances;
  }

  // ============================================================================
  // 3. SCROLL-TRIGGERED ANIMATIONS
  // ============================================================================

  class ScrollAnimations {
    constructor() {
      this.observer = null;
      this.elements = [];

      if (!prefersReducedMotion()) {
        this.init();
      }
    }

    init() {
      // Create IntersectionObserver
      this.observer = new IntersectionObserver(
        (entries) => this.handleIntersection(entries),
        {
          threshold: CONFIG.scroll.threshold,
          rootMargin: CONFIG.scroll.rootMargin,
        }
      );

      // Find and observe all animate-in elements
      this.observe();

      // Re-observe on DOM changes
      const mutationObserver = new MutationObserver(
        debounce(() => this.observe(), 100)
      );
      mutationObserver.observe(document.body, { childList: true, subtree: true });
    }

    observe() {
      const elements = document.querySelectorAll(
        '.animate-in:not(.is-visible), [data-animate]:not(.is-visible)'
      );

      elements.forEach((el) => {
        if (!this.elements.includes(el)) {
          this.elements.push(el);
          this.observer.observe(el);
        }
      });
    }

    handleIntersection(entries) {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const el = entry.target;

          // Apply animation class
          el.classList.add('is-visible');

          // Handle custom animation type
          const animationType = el.dataset.animate;
          if (animationType) {
            el.classList.add(`animate-${animationType}`);
          }

          // Unobserve after animation
          this.observer.unobserve(el);
        }
      });
    }

    destroy() {
      if (this.observer) {
        this.observer.disconnect();
      }
    }
  }

  // ============================================================================
  // 4. STAGGER ANIMATION HELPER
  // ============================================================================

  class StaggerAnimation {
    /**
     * Animate a group of elements with staggered timing
     * @param {NodeList|Array} elements - Elements to animate
     * @param {Object} options - Animation options
     */
    static animate(elements, options = {}) {
      const {
        delay = CONFIG.stagger.baseDelay,
        duration = 500,
        easing = 'easeOutExpo',
        animation = 'fadeUp',
        startDelay = 0,
        onComplete = null,
      } = options;

      if (prefersReducedMotion()) {
        elements.forEach((el) => {
          el.style.opacity = '1';
          el.style.transform = 'none';
        });
        if (onComplete) onComplete();
        return;
      }

      const easingFn = Easing[easing] || Easing.easeOutExpo;

      elements.forEach((el, index) => {
        const itemDelay = startDelay + index * delay;

        // Set initial state
        el.style.opacity = '0';
        el.style.transition = 'none';

        switch (animation) {
          case 'fadeUp':
            el.style.transform = 'translateY(30px)';
            break;
          case 'fadeDown':
            el.style.transform = 'translateY(-30px)';
            break;
          case 'fadeLeft':
            el.style.transform = 'translateX(30px)';
            break;
          case 'fadeRight':
            el.style.transform = 'translateX(-30px)';
            break;
          case 'scaleIn':
            el.style.transform = 'scale(0.9)';
            break;
          default:
            el.style.transform = 'translateY(30px)';
        }

        // Trigger animation after delay
        setTimeout(() => {
          el.style.transition = `opacity ${duration}ms ${easing}, transform ${duration}ms ${easing}`;
          el.style.opacity = '1';
          el.style.transform = 'translateY(0) translateX(0) scale(1)';

          // Call onComplete after last item
          if (index === elements.length - 1 && onComplete) {
            setTimeout(onComplete, duration);
          }
        }, itemDelay);
      });
    }

    /**
     * Set up stagger animation for elements with data attributes
     */
    static init() {
      const containers = document.querySelectorAll('[data-stagger]');

      containers.forEach((container) => {
        const elements = container.querySelectorAll('[data-stagger-item]');
        const delay = parseInt(container.dataset.stagger) || CONFIG.stagger.baseDelay;
        const animation = container.dataset.staggerAnimation || 'fadeUp';

        // Use IntersectionObserver to trigger when container is visible
        const observer = new IntersectionObserver(
          (entries) => {
            entries.forEach((entry) => {
              if (entry.isIntersecting) {
                StaggerAnimation.animate(elements, { delay, animation });
                observer.unobserve(container);
              }
            });
          },
          { threshold: 0.1 }
        );

        observer.observe(container);
      });
    }
  }

  // ============================================================================
  // 5. SMOOTH SCROLL TO ANCHORS
  // ============================================================================

  class SmoothScroll {
    constructor() {
      if (prefersReducedMotion()) return;
      this.init();
    }

    init() {
      // Handle all anchor links
      document.addEventListener('click', (e) => {
        const link = e.target.closest('a[href^="#"]');
        if (!link) return;

        const targetId = link.getAttribute('href');
        if (targetId === '#') return;

        const target = document.querySelector(targetId);
        if (!target) return;

        e.preventDefault();

        // Get offset from data attribute or default to header height
        const offset = parseInt(link.dataset.scrollOffset) || 80;

        this.scrollTo(target, offset);

        // Update URL without jumping
        history.pushState(null, null, targetId);
      });
    }

    /**
     * Smooth scroll to element
     * @param {Element} target - Target element
     * @param {number} offset - Offset from top
     */
    scrollTo(target, offset = 80) {
      const targetPosition =
        target.getBoundingClientRect().top + window.pageYOffset - offset;
      const startPosition = window.pageYOffset;
      const distance = targetPosition - startPosition;
      const duration = CONFIG.smoothScroll.duration;
      const easingFn =
        Easing[CONFIG.smoothScroll.easing] || Easing.easeOutExpo;

      let startTime = null;

      function animate(currentTime) {
        if (startTime === null) startTime = currentTime;
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const easedProgress = easingFn(progress);

        window.scrollTo(0, startPosition + distance * easedProgress);

        if (elapsed < duration) {
          requestAnimationFrame(animate);
        }
      }

      requestAnimationFrame(animate);
    }

    /**
     * Scroll to top of page
     */
    scrollToTop() {
      this.scrollTo(document.body, 0);
    }
  }

  // ============================================================================
  // 6. VIEW TRANSITION HELPER
  // ============================================================================

  class ViewTransitions {
    constructor() {
      this.isTransitioning = false;
      this.init();
    }

    init() {
      // Handle navigation links with transition
      document.addEventListener('click', async (e) => {
        const link = e.target.closest('a[data-transition]');
        if (!link) return;

        const href = link.getAttribute('href');
        if (!href || href.startsWith('#') || href.startsWith('javascript:')) return;

        // Check if it's same-origin
        try {
          const url = new URL(href, window.location.origin);
          if (url.origin !== window.location.origin) return;
        } catch {
          return;
        }

        e.preventDefault();

        await this.transition(href, link.dataset.transition || 'fade');
      });
    }

    /**
     * Perform page transition
     * @param {string} url - Target URL
     * @param {string} type - Transition type
     */
    async transition(url, type = 'fade') {
      if (this.isTransitioning) return;
      this.isTransitioning = true;

      // Check for native View Transitions API support
      if (document.startViewTransition && !prefersReducedMotion()) {
        try {
          const transition = document.startViewTransition(async () => {
            const response = await fetch(url);
            const html = await response.text();
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');

            // Replace content
            document.documentElement.innerHTML = doc.documentElement.innerHTML;

            // Update URL
            history.pushState(null, doc.title, url);
            document.title = doc.title;

            // Re-initialize effects
            NightFlowEffects.reinit();
          });

          await transition.finished;
        } catch (error) {
          console.error('View transition failed:', error);
          window.location.href = url;
        }
      } else {
        // Fallback for browsers without View Transitions API
        await this.fallbackTransition(url, type);
      }

      this.isTransitioning = false;
    }

    /**
     * Fallback transition for older browsers
     */
    async fallbackTransition(url, type) {
      const overlay = document.createElement('div');
      overlay.style.cssText = `
        position: fixed;
        inset: 0;
        background: var(--bg-primary, #000);
        z-index: 99999;
        opacity: 0;
        transition: opacity 0.3s ease;
        pointer-events: none;
      `;
      document.body.appendChild(overlay);

      // Fade out
      await new Promise((resolve) => {
        requestAnimationFrame(() => {
          overlay.style.opacity = '1';
          setTimeout(resolve, 300);
        });
      });

      // Navigate
      window.location.href = url;
    }

    /**
     * Add view transition names to elements for cross-page animations
     * @param {Element} element - Element to name
     * @param {string} name - Unique transition name
     */
    static setTransitionName(element, name) {
      element.style.viewTransitionName = name;
    }
  }

  // ============================================================================
  // 7. PARALLAX EFFECT
  // ============================================================================

  class ParallaxEffect {
    constructor() {
      this.elements = [];
      this.rafId = null;
      this.lastScrollY = 0;

      if (!prefersReducedMotion()) {
        this.init();
      }
    }

    init() {
      this.elements = Array.from(document.querySelectorAll('[data-parallax]'));
      if (this.elements.length === 0) return;

      this.update();
      window.addEventListener('scroll', () => this.scheduleUpdate(), { passive: true });
      window.addEventListener('resize', debounce(() => this.update(), 100));
    }

    scheduleUpdate() {
      if (!this.rafId) {
        this.rafId = requestAnimationFrame(() => {
          this.update();
          this.rafId = null;
        });
      }
    }

    update() {
      const scrollY = window.pageYOffset;
      const viewportHeight = window.innerHeight;

      this.elements.forEach((el) => {
        const rect = el.getBoundingClientRect();
        const speed = parseFloat(el.dataset.parallax) || 0.5;

        // Only update if element is in viewport
        if (rect.bottom > 0 && rect.top < viewportHeight) {
          const yPos = (rect.top - viewportHeight / 2) * speed;
          el.style.transform = `translateY(${yPos}px)`;
        }
      });

      this.lastScrollY = scrollY;
    }

    destroy() {
      if (this.rafId) {
        cancelAnimationFrame(this.rafId);
      }
    }
  }

  // ============================================================================
  // 8. TILT EFFECT (for cards)
  // ============================================================================

  class TiltEffect {
    constructor(element) {
      this.element = element;
      this.maxTilt = parseFloat(element.dataset.tilt) || 10;
      this.perspective = parseFloat(element.dataset.tiltPerspective) || 1000;
      this.scale = parseFloat(element.dataset.tiltScale) || 1.02;
      this.speed = parseFloat(element.dataset.tiltSpeed) || 400;
      this.glare = element.dataset.tiltGlare === 'true';

      if (!prefersReducedMotion()) {
        this.init();
      }
    }

    init() {
      this.element.style.transformStyle = 'preserve-3d';
      this.element.style.transition = `transform ${this.speed}ms ease`;

      if (this.glare) {
        this.createGlareElement();
      }

      this.bindEvents();
    }

    createGlareElement() {
      this.glareElement = document.createElement('div');
      this.glareElement.style.cssText = `
        position: absolute;
        inset: 0;
        background: linear-gradient(
          135deg,
          rgba(255, 255, 255, 0.25) 0%,
          transparent 50%
        );
        opacity: 0;
        transition: opacity ${this.speed}ms ease;
        pointer-events: none;
        border-radius: inherit;
      `;
      this.element.style.position = 'relative';
      this.element.style.overflow = 'hidden';
      this.element.appendChild(this.glareElement);
    }

    bindEvents() {
      this.element.addEventListener('mouseenter', () => {
        this.element.style.transition = 'none';
      });

      this.element.addEventListener('mousemove', (e) => {
        const rect = this.element.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        const centerX = rect.width / 2;
        const centerY = rect.height / 2;

        const tiltX = ((y - centerY) / centerY) * -this.maxTilt;
        const tiltY = ((x - centerX) / centerX) * this.maxTilt;

        this.element.style.transform = `
          perspective(${this.perspective}px)
          rotateX(${tiltX}deg)
          rotateY(${tiltY}deg)
          scale(${this.scale})
        `;

        if (this.glareElement) {
          this.glareElement.style.opacity = '1';
          const glareX = (x / rect.width) * 100;
          const glareY = (y / rect.height) * 100;
          this.glareElement.style.background = `
            radial-gradient(
              circle at ${glareX}% ${glareY}%,
              rgba(255, 255, 255, 0.2) 0%,
              transparent 50%
            )
          `;
        }
      });

      this.element.addEventListener('mouseleave', () => {
        this.element.style.transition = `transform ${this.speed}ms ease`;
        this.element.style.transform = `
          perspective(${this.perspective}px)
          rotateX(0deg)
          rotateY(0deg)
          scale(1)
        `;

        if (this.glareElement) {
          this.glareElement.style.opacity = '0';
        }
      });
    }
  }

  // ============================================================================
  // 9. TEXT REVEAL ANIMATION
  // ============================================================================

  class TextReveal {
    /**
     * Split text into spans for animation
     * @param {Element} element - Element containing text
     * @param {string} type - Split type: 'chars', 'words', or 'lines'
     */
    static split(element, type = 'chars') {
      const text = element.textContent;
      element.textContent = '';
      element.setAttribute('aria-label', text);

      if (type === 'chars') {
        text.split('').forEach((char) => {
          const span = document.createElement('span');
          span.textContent = char === ' ' ? ' ' : char;
          span.style.display = 'inline-block';
          span.className = 'char';
          element.appendChild(span);
        });
      } else if (type === 'words') {
        text.split(' ').forEach((word, index) => {
          const span = document.createElement('span');
          span.textContent = word;
          span.style.display = 'inline-block';
          span.className = 'word';
          element.appendChild(span);
          if (index < text.split(' ').length - 1) {
            element.appendChild(document.createTextNode(' '));
          }
        });
      }

      return element.querySelectorAll(type === 'chars' ? '.char' : '.word');
    }

    /**
     * Animate text reveal
     * @param {Element} element - Element to animate
     * @param {Object} options - Animation options
     */
    static reveal(element, options = {}) {
      const {
        type = 'chars',
        animation = 'fadeUp',
        stagger = 30,
        duration = 500,
      } = options;

      if (prefersReducedMotion()) {
        element.style.opacity = '1';
        return;
      }

      const items = this.split(element, type);

      StaggerAnimation.animate(items, {
        delay: stagger,
        duration,
        animation,
      });
    }

    /**
     * Initialize text reveals from data attributes
     */
    static init() {
      const elements = document.querySelectorAll('[data-text-reveal]');

      elements.forEach((el) => {
        const type = el.dataset.textReveal || 'chars';
        const animation = el.dataset.textAnimation || 'fadeUp';
        const stagger = parseInt(el.dataset.textStagger) || 30;

        // Use IntersectionObserver to trigger when visible
        const observer = new IntersectionObserver(
          (entries) => {
            entries.forEach((entry) => {
              if (entry.isIntersecting) {
                TextReveal.reveal(el, { type, animation, stagger });
                observer.unobserve(el);
              }
            });
          },
          { threshold: 0.1 }
        );

        observer.observe(el);
      });
    }
  }

  // ============================================================================
  // 10. COUNTER ANIMATION
  // ============================================================================

  class CounterAnimation {
    /**
     * Animate a number counter
     * @param {Element} element - Element to animate
     * @param {Object} options - Animation options
     */
    static animate(element, options = {}) {
      const {
        start = 0,
        end = parseInt(element.textContent) || 100,
        duration = 2000,
        easing = 'easeOutExpo',
        prefix = '',
        suffix = '',
        decimals = 0,
        separator = ',',
      } = options;

      if (prefersReducedMotion()) {
        element.textContent = prefix + this.formatNumber(end, decimals, separator) + suffix;
        return;
      }

      const easingFn = Easing[easing] || Easing.easeOutExpo;
      let startTime = null;

      const animate = (currentTime) => {
        if (startTime === null) startTime = currentTime;
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const easedProgress = easingFn(progress);

        const currentValue = start + (end - start) * easedProgress;
        element.textContent =
          prefix + this.formatNumber(currentValue, decimals, separator) + suffix;

        if (progress < 1) {
          requestAnimationFrame(animate);
        }
      };

      requestAnimationFrame(animate);
    }

    /**
     * Format number with decimals and separator
     */
    static formatNumber(value, decimals, separator) {
      const fixed = value.toFixed(decimals);
      const parts = fixed.split('.');
      parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, separator);
      return parts.join('.');
    }

    /**
     * Initialize counters from data attributes
     */
    static init() {
      const elements = document.querySelectorAll('[data-counter]');

      elements.forEach((el) => {
        const observer = new IntersectionObserver(
          (entries) => {
            entries.forEach((entry) => {
              if (entry.isIntersecting) {
                CounterAnimation.animate(el, {
                  end: parseInt(el.dataset.counter) || parseInt(el.textContent),
                  duration: parseInt(el.dataset.counterDuration) || 2000,
                  prefix: el.dataset.counterPrefix || '',
                  suffix: el.dataset.counterSuffix || '',
                  decimals: parseInt(el.dataset.counterDecimals) || 0,
                });
                observer.unobserve(el);
              }
            });
          },
          { threshold: 0.5 }
        );

        observer.observe(el);
      });
    }
  }

  // ============================================================================
  // MAIN INITIALIZATION
  // ============================================================================

  const NightFlowEffects = {
    cursor: null,
    magneticElements: [],
    scrollAnimations: null,
    smoothScroll: null,
    viewTransitions: null,
    parallax: null,
    tiltElements: [],

    /**
     * Initialize all effects
     */
    init() {
      // Wait for DOM to be ready
      if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => this.setup());
      } else {
        this.setup();
      }
    },

    /**
     * Setup all effects
     */
    setup() {
      // Custom cursor
      if (CONFIG.cursor.enabled) {
        this.cursor = new CustomCursor();
      }

      // Magnetic buttons
      this.magneticElements = initMagneticElements();

      // Scroll animations
      this.scrollAnimations = new ScrollAnimations();

      // Stagger animations
      StaggerAnimation.init();

      // Smooth scroll
      this.smoothScroll = new SmoothScroll();

      // View transitions
      this.viewTransitions = new ViewTransitions();

      // Parallax
      this.parallax = new ParallaxEffect();

      // Tilt effects
      document.querySelectorAll('[data-tilt]').forEach((el) => {
        this.tiltElements.push(new TiltEffect(el));
      });

      // Text reveal
      TextReveal.init();

      // Counter animations
      CounterAnimation.init();

      // Log initialization
      console.log('NightFlow Effects initialized');
    },

    /**
     * Reinitialize effects (useful after page transitions)
     */
    reinit() {
      // Re-observe new animate-in elements
      if (this.scrollAnimations) {
        this.scrollAnimations.observe();
      }

      // Re-init magnetic elements
      this.magneticElements = initMagneticElements();

      // Re-init stagger animations
      StaggerAnimation.init();

      // Re-init tilt effects
      document.querySelectorAll('[data-tilt]:not([data-tilt-init])').forEach((el) => {
        el.dataset.tiltInit = 'true';
        this.tiltElements.push(new TiltEffect(el));
      });

      // Re-init text reveal
      TextReveal.init();

      // Re-init counters
      CounterAnimation.init();
    },

    /**
     * Destroy all effects (cleanup)
     */
    destroy() {
      if (this.cursor) this.cursor.destroy();
      if (this.scrollAnimations) this.scrollAnimations.destroy();
      if (this.parallax) this.parallax.destroy();
      this.magneticElements.forEach((el) => el.destroy?.());
    },

    // Expose utility functions
    utils: {
      lerp,
      clamp,
      distance,
      mapRange,
      debounce,
      throttle,
      Easing,
    },

    // Expose classes for external use
    classes: {
      CustomCursor,
      MagneticElement,
      ScrollAnimations,
      StaggerAnimation,
      SmoothScroll,
      ViewTransitions,
      ParallaxEffect,
      TiltEffect,
      TextReveal,
      CounterAnimation,
    },
  };

  // Auto-initialize
  NightFlowEffects.init();

  // Export to global scope
  window.NightFlowEffects = NightFlowEffects;

  // ============================================================================
  // TOAST NOTIFICATION SYSTEM
  // ============================================================================

  const ToastSystem = {
    container: null,
    queue: [],

    init() {
      if (this.container) return;

      // Create toast container
      this.container = document.createElement('div');
      this.container.className = 'toast-container';
      this.container.style.cssText = `
        position: fixed;
        bottom: 24px;
        right: 24px;
        z-index: 10000;
        display: flex;
        flex-direction: column-reverse;
        gap: 12px;
        pointer-events: none;
      `;
      document.body.appendChild(this.container);

      // Add CSS for toasts
      if (!document.getElementById('toast-styles')) {
        const style = document.createElement('style');
        style.id = 'toast-styles';
        style.textContent = `
          .nf-toast {
            background: rgba(15, 31, 53, 0.95);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 14px;
            padding: 16px 20px;
            display: flex;
            align-items: center;
            gap: 14px;
            min-width: 280px;
            max-width: 400px;
            transform: translateX(120%);
            opacity: 0;
            transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
            pointer-events: auto;
            box-shadow: 0 16px 48px rgba(0, 0, 0, 0.4);
          }
          .nf-toast.show {
            transform: translateX(0);
            opacity: 1;
          }
          .nf-toast-icon {
            width: 36px;
            height: 36px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            flex-shrink: 0;
          }
          .nf-toast-success .nf-toast-icon { background: rgba(78, 205, 196, 0.15); color: #4ECDC4; }
          .nf-toast-error .nf-toast-icon { background: rgba(255, 107, 107, 0.15); color: #FF6B6B; }
          .nf-toast-warning .nf-toast-icon { background: rgba(255, 217, 61, 0.15); color: #FFD93D; }
          .nf-toast-info .nf-toast-icon { background: rgba(78, 205, 196, 0.15); color: #4ECDC4; }
          .nf-toast-content { flex: 1; min-width: 0; }
          .nf-toast-title {
            font-family: 'Syne', sans-serif;
            font-size: 15px;
            font-weight: 600;
            color: #F0F4F8;
            margin-bottom: 2px;
          }
          .nf-toast-message {
            font-size: 13px;
            color: rgba(176, 190, 197, 0.9);
            line-height: 1.4;
          }
          .nf-toast-close {
            width: 28px;
            height: 28px;
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.05);
            border: none;
            color: rgba(176, 190, 197, 0.7);
            font-size: 14px;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
          }
          .nf-toast-close:hover { background: rgba(255, 255, 255, 0.1); color: #F0F4F8; }
          .nf-toast-progress {
            position: absolute;
            bottom: 0;
            left: 0;
            height: 3px;
            background: linear-gradient(90deg, #FF6B6B, #FFD93D);
            border-radius: 0 0 14px 14px;
            transition: width linear;
          }
          .nf-toast-success .nf-toast-progress { background: linear-gradient(90deg, #4ECDC4, #45B7AA); }
          @media (max-width: 480px) {
            .toast-container { left: 16px; right: 16px; bottom: 16px; }
            .nf-toast { min-width: auto; }
          }
        `;
        document.head.appendChild(style);
      }
    },

    show(title, message = '', type = 'info', duration = 4000) {
      this.init();

      const icons = {
        success: '✓',
        error: '✗',
        warning: '⚠',
        info: 'ℹ'
      };

      const toast = document.createElement('div');
      toast.className = `nf-toast nf-toast-${type}`;
      toast.style.position = 'relative';
      toast.innerHTML = `
        <div class="nf-toast-icon">${icons[type] || icons.info}</div>
        <div class="nf-toast-content">
          <div class="nf-toast-title">${title}</div>
          ${message ? `<div class="nf-toast-message">${message}</div>` : ''}
        </div>
        <button class="nf-toast-close">✕</button>
        <div class="nf-toast-progress" style="width: 100%"></div>
      `;

      this.container.appendChild(toast);

      // Close button handler
      const closeBtn = toast.querySelector('.nf-toast-close');
      closeBtn.addEventListener('click', () => this.dismiss(toast));

      // Show animation
      requestAnimationFrame(() => {
        toast.classList.add('show');
        // Start progress bar animation
        const progress = toast.querySelector('.nf-toast-progress');
        progress.style.transitionDuration = `${duration}ms`;
        requestAnimationFrame(() => {
          progress.style.width = '0%';
        });
      });

      // Auto dismiss
      const timeoutId = setTimeout(() => this.dismiss(toast), duration);

      // Pause on hover
      toast.addEventListener('mouseenter', () => {
        clearTimeout(timeoutId);
        const progress = toast.querySelector('.nf-toast-progress');
        const computed = getComputedStyle(progress);
        progress.style.transitionDuration = '0ms';
        progress.style.width = computed.width;
      });

      toast.addEventListener('mouseleave', () => {
        const progress = toast.querySelector('.nf-toast-progress');
        const currentWidth = parseFloat(progress.style.width);
        const remainingTime = (currentWidth / 100) * duration;
        progress.style.transitionDuration = `${remainingTime}ms`;
        progress.style.width = '0%';
        setTimeout(() => this.dismiss(toast), remainingTime);
      });

      return toast;
    },

    dismiss(toast) {
      toast.classList.remove('show');
      setTimeout(() => toast.remove(), 350);
    },

    success(title, message = '', duration = 4000) {
      return this.show(title, message, 'success', duration);
    },

    error(title, message = '', duration = 5000) {
      return this.show(title, message, 'error', duration);
    },

    warning(title, message = '', duration = 4500) {
      return this.show(title, message, 'warning', duration);
    },

    info(title, message = '', duration = 4000) {
      return this.show(title, message, 'info', duration);
    }
  };

  // ============================================================================
  // SHARE FUNCTIONALITY
  // ============================================================================

  const ShareUtils = {
    async share(data) {
      const { title, text, url } = data;

      // Try native Web Share API first
      if (navigator.share) {
        try {
          await navigator.share({ title, text, url });
          return { success: true, method: 'native' };
        } catch (err) {
          if (err.name !== 'AbortError') {
            console.warn('Native share failed, falling back to clipboard');
          }
        }
      }

      // Fallback to clipboard
      return this.copyToClipboard(url);
    },

    async copyToClipboard(text) {
      try {
        await navigator.clipboard.writeText(text);
        ToastSystem.success('Link Copied!', 'Share it with your friends');
        return { success: true, method: 'clipboard' };
      } catch (err) {
        // Fallback for older browsers
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.cssText = 'position:fixed;left:-9999px;top:-9999px';
        document.body.appendChild(textarea);
        textarea.select();
        try {
          document.execCommand('copy');
          ToastSystem.success('Link Copied!', 'Share it with your friends');
          return { success: true, method: 'execCommand' };
        } catch {
          ToastSystem.error('Copy Failed', 'Please copy the link manually');
          return { success: false };
        } finally {
          textarea.remove();
        }
      }
    },

    shareVenue(venueId, venueName) {
      const url = `${window.location.origin}/venue.html?id=${venueId}`;
      this.share({
        title: venueName,
        text: `Check out ${venueName} on NightFlow`,
        url
      });
    },

    shareEvent(eventId, eventTitle) {
      const url = `${window.location.origin}/event.html?id=${eventId}`;
      this.share({
        title: eventTitle,
        text: `Join me at ${eventTitle}!`,
        url
      });
    },

    shareToWhatsApp(text, url) {
      const msg = encodeURIComponent(`${text} ${url}`);
      window.open(`https://wa.me/?text=${msg}`, '_blank');
    },

    shareToTwitter(text, url) {
      const tweet = encodeURIComponent(text);
      const link = encodeURIComponent(url);
      window.open(`https://twitter.com/intent/tweet?text=${tweet}&url=${link}`, '_blank');
    },

    shareToFacebook(url) {
      const link = encodeURIComponent(url);
      window.open(`https://www.facebook.com/sharer/sharer.php?u=${link}`, '_blank');
    }
  };

  // ============================================================================
  // FORM VALIDATION UTILITIES
  // ============================================================================

  const FormValidation = {
    patterns: {
      email: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
      phone: /^[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}$/,
      password: /^.{6,}$/,
      name: /^[a-zA-ZͰ-Ͽἀ-῿\s]{2,}$/
    },

    validate(value, type) {
      if (!value || !value.trim()) return { valid: false, error: 'This field is required' };

      switch (type) {
        case 'email':
          return this.patterns.email.test(value)
            ? { valid: true }
            : { valid: false, error: 'Please enter a valid email' };
        case 'password':
          return value.length >= 6
            ? { valid: true }
            : { valid: false, error: 'Password must be at least 6 characters' };
        case 'name':
          return value.trim().length >= 2
            ? { valid: true }
            : { valid: false, error: 'Name must be at least 2 characters' };
        case 'phone':
          return !value || this.patterns.phone.test(value)
            ? { valid: true }
            : { valid: false, error: 'Please enter a valid phone number' };
        default:
          return { valid: true };
      }
    },

    showFieldError(input, message) {
      this.clearFieldError(input);

      const wrapper = input.closest('.form-group') || input.parentElement;
      const errorEl = document.createElement('div');
      errorEl.className = 'field-error';
      errorEl.textContent = message;
      errorEl.style.cssText = `
        color: #FF6B6B;
        font-size: 12px;
        margin-top: 6px;
        animation: fadeIn 0.2s ease;
      `;

      wrapper.appendChild(errorEl);
      input.style.borderColor = '#FF6B6B';
      input.classList.add('input-error');
    },

    clearFieldError(input) {
      const wrapper = input.closest('.form-group') || input.parentElement;
      const existing = wrapper.querySelector('.field-error');
      if (existing) existing.remove();
      input.style.borderColor = '';
      input.classList.remove('input-error');
    },

    validateForm(form, fields) {
      let isValid = true;

      fields.forEach(({ input, type }) => {
        const result = this.validate(input.value, type);
        if (!result.valid) {
          this.showFieldError(input, result.error);
          isValid = false;
        } else {
          this.clearFieldError(input);
        }
      });

      return isValid;
    }
  };

  // ============================================================================
  // LOADING STATE UTILITIES
  // ============================================================================

  const LoadingState = {
    set(button, loading, loadingText = 'Loading...') {
      if (loading) {
        button.dataset.originalText = button.innerHTML;
        button.disabled = true;
        button.innerHTML = `
          <span class="btn-spinner" style="
            display: inline-block;
            width: 16px;
            height: 16px;
            border: 2px solid rgba(255,255,255,0.3);
            border-top-color: currentColor;
            border-radius: 50%;
            animation: spin 0.7s linear infinite;
            margin-right: 8px;
            vertical-align: middle;
          "></span>${loadingText}
        `;
        button.style.opacity = '0.7';
        button.style.pointerEvents = 'none';
      } else {
        button.innerHTML = button.dataset.originalText || button.innerHTML;
        button.disabled = false;
        button.style.opacity = '';
        button.style.pointerEvents = '';
      }
    }
  };

  // Add spin animation if not exists
  if (!document.getElementById('spin-animation')) {
    const style = document.createElement('style');
    style.id = 'spin-animation';
    style.textContent = '@keyframes spin { to { transform: rotate(360deg); } }';
    document.head.appendChild(style);
  }

  // ============================================================================
  // FAVORITES FUNCTIONALITY
  // ============================================================================

  const FavoritesManager = {
    getKey() {
      return 'nightflow_favorites';
    },

    getFavorites() {
      try {
        return JSON.parse(localStorage.getItem(this.getKey()) || '[]');
      } catch {
        return [];
      }
    },

    isFavorited(venueId) {
      return this.getFavorites().includes(venueId);
    },

    async toggle(venueId, button) {
      const isFavorited = this.isFavorited(venueId);
      let favorites = this.getFavorites();

      if (isFavorited) {
        favorites = favorites.filter(id => id !== venueId);
        if (button) {
          button.classList.remove('favorited');
          button.querySelector('.heart-icon')?.classList.remove('filled');
        }
        ToastSystem.info('Removed from favorites');
      } else {
        favorites.push(venueId);
        if (button) {
          button.classList.add('favorited');
          button.querySelector('.heart-icon')?.classList.add('filled');
        }
        ToastSystem.success('Added to favorites!');
      }

      localStorage.setItem(this.getKey(), JSON.stringify(favorites));

      // Try to sync with server if authenticated
      const token = localStorage.getItem('nightflow_token');
      if (token && window.NightFlowAPI) {
        try {
          if (isFavorited) {
            await NightFlowAPI.request(`/api/favorites/${venueId}`, { method: 'DELETE' });
          } else {
            await NightFlowAPI.request('/api/favorites', {
              method: 'POST',
              body: JSON.stringify({ venue_id: venueId })
            });
          }
        } catch {
          // Server sync failed, but local storage is updated
        }
      }

      return !isFavorited;
    }
  };

  // Export utilities to global scope
  window.NightFlowToast = ToastSystem;
  window.NightFlowShare = ShareUtils;
  window.NightFlowValidation = FormValidation;
  window.NightFlowLoading = LoadingState;
  window.NightFlowFavorites = FavoritesManager;

  // Global convenience function
  window.showToast = function(title, message, type = 'info') {
    return ToastSystem.show(title, message, type);
  };
})();
