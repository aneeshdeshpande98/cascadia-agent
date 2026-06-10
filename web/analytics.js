window.cascadiaAnalytics = (() => {
  let enabled = false;
  let ready = false;
  let pending = [];

  function init() {
    fetch("/api/config")
      .then((response) => response.json())
      .then((config) => {
        const posthog = config.posthog || {};
        if (!posthog.enabled || !posthog.project_key) {
          console.info("PostHog disabled: set POSTHOG_PROJECT_KEY to enable analytics.");
          return;
        }

        installPostHog(posthog.project_key, posthog.host || "https://us.i.posthog.com");
        enabled = true;
        ready = true;
        flush();
        capture("app_loaded", { analytics_enabled: true });
      })
      .catch((error) => {
        console.warn("PostHog config unavailable", error);
      });
  }

  function installPostHog(projectKey, apiHost) {
    (function (documentRef, posthogRef) {
      if (posthogRef.__SV) return;

      window.posthog = posthogRef;
      posthogRef._i = [];
      posthogRef.init = function (token, config, name) {
        function addMethod(target, methodName) {
          target[methodName] = function () {
            target.push([methodName].concat(Array.prototype.slice.call(arguments, 0)));
          };
        }

        const script = documentRef.createElement("script");
        script.type = "text/javascript";
        script.crossOrigin = "anonymous";
        script.async = true;
        script.src = config.api_host.replace(".i.posthog.com", "-assets.i.posthog.com") + "/static/array.js";
        const firstScript = documentRef.getElementsByTagName("script")[0];
        firstScript.parentNode.insertBefore(script, firstScript);

        let target = posthogRef;
        if (name !== undefined) {
          target = posthogRef[name] = [];
        } else {
          name = "posthog";
        }
        target.people = target.people || [];
        [
          "capture",
          "identify",
          "reset",
          "debug",
          "opt_in_capturing",
          "opt_out_capturing",
          "has_opted_out_capturing",
          "get_distinct_id",
          "get_session_id",
        ].forEach((methodName) => addMethod(target, methodName));
        posthogRef._i.push([token, config, name]);
      };
      posthogRef.__SV = 1;
    })(document, window.posthog || []);

    window.posthog.init(projectKey, {
      api_host: apiHost,
      defaults: "2026-01-30",
      capture_pageview: true,
      autocapture: true,
    });
  }

  function capture(eventName, properties = {}) {
    const safeProperties = sanitizeProperties(properties);
    if (!enabled || !ready || !window.posthog || !window.posthog.capture) {
      pending.push([eventName, safeProperties]);
      return;
    }
    window.posthog.capture(eventName, safeProperties);
  }

  function flush() {
    const queued = pending;
    pending = [];
    queued.forEach(([eventName, properties]) => capture(eventName, properties));
  }

  function sanitizeProperties(properties) {
    return Object.fromEntries(
      Object.entries(properties).filter(([, value]) => (
        value === null
        || ["string", "number", "boolean"].includes(typeof value)
        || Array.isArray(value)
      ))
    );
  }

  init();

  return {
    capture,
    isEnabled: () => enabled,
  };
})();
