async def context_add_init_script(browser, browser_settings):
    user_agent = browser_settings.get('user_agent', '')
    width = browser_settings.get('width', 1920)
    height = browser_settings.get('height', 1080)
    proxy = browser_settings.get('proxy')
    languages = browser_settings.get('languages', ['en-US', 'en'])
    if proxy:
        context = await browser.new_context(
            user_agent=user_agent,
            permissions=['camera', 'microphone'],
            viewport={'width': width, 'height': height},
            proxy=proxy
        )
    else:
        context = await browser.new_context(
            user_agent=user_agent,
            permissions=['camera', 'microphone'],
            viewport={'width': width, 'height': height}
        )
    context_add_navigator = """
            Object.defineProperty(navigator, 'languages', { get: () => $languages });
            Object.defineProperty(window.screen, 'availWidth', { get: () => $width });
            Object.defineProperty(window.screen, 'availHeight', { get: () => $height });
            Object.defineProperty(window.screen, 'width', { get: () => $width });
            Object.defineProperty(window.screen, 'height', { get: () => $height });
            Object.defineProperty(navigator, 'userAgent', { get: () => $user_agent })
        """
    context_add_navigator = context_add_navigator.replace('$languages', str(languages)).replace('$width', str(width)).replace('$height', str(height)).replace('$user_agent', user_agent)
    await context.add_init_script(context_add_navigator)
    await context.add_init_script("""
        Object.defineProperty(navigator, 'maxTouchPoints', { get: () => 1 });
        Object.defineProperty(navigator, 'platform', { get: () => 'Win32' });
        Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 4 });
        if (navigator.connection){
            Object.defineProperty(navigator.connection, 'rtt', {get: () => 100});
        }
        window.chrome = {
            app: {
                isInstalled: false,
            },
            webstore: {
                onInstallStageChanged: {},
                onDownloadProgress: {},
            },
            runtime: {
                PlatformOs: {
                    MAC: 'mac',
                    WIN: 'win',
                    ANDROID: 'android',
                    CROS: 'cros',
                    LINUX: 'linux',
                    OPENBSD: 'openbsd',
                },
                PlatformArch: {
                    ARM: 'arm',
                    X86_32: 'x86-32',
                    X86_64: 'x86-64',
                },
                PlatformNaclArch: {
                    ARM: 'arm',
                    X86_32: 'x86-32',
                    X86_64: 'x86-64',
                },
                RequestUpdateCheckStatus: {
                    THROTTLED: 'throttled',
                    NO_UPDATE: 'no_update',
                    UPDATE_AVAILABLE: 'update_available',
                },
                OnInstalledReason: {
                    INSTALL: 'install',
                    UPDATE: 'update',
                    CHROME_UPDATE: 'chrome_update',
                    SHARED_MODULE_UPDATE: 'shared_module_update',
                },
                OnRestartRequiredReason: {
                    APP_UPDATE: 'app_update',
                    OS_UPDATE: 'os_update',
                    PERIODIC: 'periodic',
                },
            }
        };
        const originalQuery = navigator.permissions.query;
        navigator.permissions.query = (parameters) =>
            parameters.name === 'notifications'
            ? Promise.resolve({ state: 'denied' })
            : originalQuery(parameters);
        const origGetContext = HTMLCanvasElement.prototype.getContext;
        HTMLCanvasElement.prototype.getContext = function(type, ...args) {
            if (type === '2d') {
                const ctx = origGetContext.call(this, type, ...args);
                const origFillText = ctx.fillText;
                ctx.fillText = function(...args) {
                    origFillText.call(ctx, ...args);
                };
                return ctx;
            }
            return origGetContext.call(this, type, ...args);
        };
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            if (parameter === 37445) {
                return 'Google Inc.';
            }
            if (parameter === 37446) {
                return 'ANGLE (Intel(R) HD Graphics Family Direct3D11 vs_5_0 ps_5_0)';
            }
            return getParameter.call(this, parameter);
        };

        const toDataURL = HTMLCanvasElement.prototype.toDataURL;
        HTMLCanvasElement.prototype.toDataURL = function(type, ...args) {
            if (type === 'image/webp') {
                return '';
            }
            return toDataURL.call(this, type, ...args);
        };
    """)
    return context
