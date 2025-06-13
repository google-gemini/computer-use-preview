import { expect } from "chai";
import sinon, { SinonStub, SinonFakeTimers } from "sinon";
import puppeteer, { Browser, Page, KeyInput } from "puppeteer";
import {
    BrowserShell,
    OsShell,
    ScreenResolution,
    ComputerShell,
} from "../browser";
import { Command } from "../command";

const mockPage = {
    goto: sinon.stub(),
    mouse: {
        click: sinon.stub(),
        move: sinon.stub(),
        wheel: sinon.stub(),
        down: sinon.stub(),
        up: sinon.stub(),
    },
    keyboard: {
        type: sinon.stub(),
        press: sinon.stub(),
        down: sinon.stub(),
        up: sinon.stub(),
    },
    setViewport: sinon.stub(),
    waitForNavigation: sinon.stub(),
    goBack: sinon.stub(),
    goForward: sinon.stub(),
    url: sinon.stub(),
    screenshot: sinon.stub(),
    close: sinon.stub(),
    viewport: sinon.stub()
} as unknown as Page;

const mockBrowser = {
    newPage: sinon.stub().resolves(mockPage),
    close: sinon.stub().resolves(),
} as unknown as Browser;

let puppeteerLaunchStub: SinonStub;

let mockOsShellInstance: ComputerShell;
let osShellRunCommandStub: SinonStub;
let osShellScreenshotStub: SinonStub;
let osShellCurrentUrlStub: SinonStub;

describe("BrowserShell", () => {
    let browserShell: BrowserShell;
    let clock: SinonFakeTimers;

    before(() => {
        // Stub puppeteer.launch once for the entire suite
        puppeteerLaunchStub = sinon.stub(puppeteer, "launch").resolves(mockBrowser);
    });

    after(() => {
        // Restore the original puppeteer.launch after all tests
        puppeteerLaunchStub.restore();
    });

    beforeEach(() => {
        // Reset history and behavior of all stubs before each test
        puppeteerLaunchStub.resetHistory();
        puppeteerLaunchStub.resolves(mockBrowser); // Ensure it resolves with the mockBrowser

        (mockBrowser.newPage as SinonStub).resetHistory();
        (mockBrowser.newPage as SinonStub).resolves(mockPage);
        (mockBrowser.close as SinonStub).resetHistory();

        const pageStubs = [
            mockPage.goto,
            mockPage.mouse.click,
            mockPage.mouse.move,
            mockPage.mouse.wheel,
            mockPage.mouse.down,
            mockPage.mouse.up,
            mockPage.keyboard.type,
            mockPage.keyboard.press,
            mockPage.keyboard.down,
            mockPage.keyboard.up,
            mockPage.setViewport,
            mockPage.waitForNavigation,
            mockPage.goBack,
            mockPage.goForward,
            mockPage.url,
            mockPage.screenshot,
            mockPage.close,
        ];
        pageStubs.forEach((stub) => (stub as SinonStub).resetHistory());

        // Default behaviors for stubs that resolve promises or return values
        (mockPage.goto as SinonStub).resolves(null); // Puppeteer's goto returns Promise<HTTPResponse | null>
        (mockPage.mouse.click as SinonStub).resolves(undefined);
        (mockPage.mouse.move as SinonStub).resolves(undefined);
        (mockPage.mouse.wheel as SinonStub).resolves(undefined);
        (mockPage.mouse.down as SinonStub).resolves(undefined);
        (mockPage.mouse.up as SinonStub).resolves(undefined);
        (mockPage.keyboard.type as SinonStub).resolves(undefined);
        (mockPage.keyboard.press as SinonStub).resolves(undefined);
        (mockPage.keyboard.down as SinonStub).resolves(undefined);
        (mockPage.keyboard.up as SinonStub).resolves(undefined);
        (mockPage.setViewport as SinonStub).resolves(undefined);
        (mockPage.waitForNavigation as SinonStub).resolves(null);
        (mockPage.goBack as SinonStub).resolves(null);
        (mockPage.goForward as SinonStub).resolves(null);
        (mockPage.url as SinonStub).returns("http://fakeurl.com");
        (mockPage.screenshot as SinonStub).resolves("base64screenshotdata");
        (mockPage.close as SinonStub).resolves(undefined);

        // Mock OsShell instance and its methods
        osShellRunCommandStub = sinon.stub().resolves();
        osShellScreenshotStub = sinon.stub().resolves("os_shell_screenshot_data");
        osShellCurrentUrlStub = sinon.stub().returns("os_shell_url"); // Though not directly used by BrowserShell logic much

        // Create a mock OsShell instance that BrowserShell might create or use
        // This approach is for testing delegation.
        // We'll assign this to browserShell.headfulShell in headful tests.
        mockOsShellInstance = {
            runCommand: osShellRunCommandStub,
            screenshot: osShellScreenshotStub,
            currentUrl: osShellCurrentUrlStub,
        };

        clock = sinon.useFakeTimers();
    });

    afterEach(() => {
        clock.restore();
        // It's good practice to restore all stubs if they were created within beforeEach,
        // but since puppeteer.launch is global for the suite, only reset its history/behavior.
        // Individual method stubs on mocks are reset in beforeEach.
    });

    describe("init", () => {
        const resolution: ScreenResolution = { width: 1920, height: 1080 };

        it("should launch puppeteer with correct options for headless mode", async () => {
            await BrowserShell.init(true, resolution, "bn-BD,bn");
            expect(puppeteerLaunchStub.calledOnce).to.be.true;
            expect(puppeteerLaunchStub.firstCall.args[0]).to.deep.include({
                executablePath: "/usr/bin/google-chrome-stable",
                headless: true,
            });
            expect(puppeteerLaunchStub.firstCall.args[0].args).to.deep.equal([
                "--no-sandbox",
                "--disable-gpu",
                "--disable-blink-features=AutomationControlled",
                "--lang=bn-BD,bn"
            ]);
            expect(
                puppeteerLaunchStub.firstCall.args[0].ignoreDefaultArgs
            ).to.deep.equal(["--enable-automation"]);
            expect((mockBrowser.newPage as SinonStub).calledOnce).to.be.true;
            expect((mockPage.setViewport as SinonStub).calledOnceWith(resolution)).to
                .be.true;
        });

        it("should launch puppeteer with headless false for headful mode", async () => {
            await BrowserShell.init(false, resolution, 'en-US');
            expect(puppeteerLaunchStub.calledOnce).to.be.true;
            expect(puppeteerLaunchStub.firstCall.args[0]).to.deep.include({
                headless: false,
            });
        });

        it("should return a BrowserShell instance correctly initialized", async () => {
            const shell = await BrowserShell.init(true, resolution, 'en-US');
            expect(shell).to.be.instanceOf(BrowserShell);
            expect(shell.browser).to.equal(mockBrowser);
            expect(shell.page).to.equal(mockPage);
            expect(shell.headfulShell).to.be.undefined; // For headless true
        });

        it("should instantiate OsShell via constructor if headless is false", () => {
            // This tests the constructor logic passed from init's typical usage.
            // We can't easily mock `new OsShell()` without changing BrowserShell or using proxyquire.
            // So, we check if headfulShell is an instance of OsShell (the real one).
            const shell = new BrowserShell(mockBrowser, mockPage, false); // headless: false
            expect(shell.headfulShell).to.be.instanceOf(OsShell);
        });
    });

    describe("runCommand (headless mode)", () => {
        beforeEach(() => {
            browserShell = new BrowserShell(mockBrowser, mockPage, true); // headless = true
            expect(browserShell.headfulShell).to.be.undefined;
        });

        it("should handle open_web_browser", async () => {
            const command: Command = { name: "open_web_browser" };
            await browserShell.runCommand(command);
            expect(
                (mockPage.goto as SinonStub).calledOnceWith("https://www.google.com")
            ).to.be.true;
        });

        it("should handle click_at with delay", async () => {
            const command: Command = { name: "click_at", args: { x: 100, y: 200 } };
            const promise = browserShell.runCommand(command);
            expect((mockPage.mouse.click as SinonStub).calledOnceWith(100, 200)).to.be
                .true;
            await clock.tickAsync(300); // Advance timer for the delay
            await promise;
        });

        it("should handle hover_at", async () => {
            const command: Command = { name: "hover_at", args: { x: 150, y: 250 } };
            await browserShell.runCommand(command);
            expect((mockPage.mouse.move as SinonStub).calledOnceWith(150, 250)).to.be
                .true;
        });

        it("should handle type_text_at with delays and Enter press", async () => {
            const command: Command = {
                name: "type_text_at",
                args: {
                    x: 50,
                    y: 60,
                    text: "hi",
                    press_enter: true,
                    clear_before_typing: false,
                },
            };

            const commandPromise = browserShell.runCommand(command);
            await clock.runAllAsync();
            await commandPromise;

            expect(
                (mockPage.mouse.click as SinonStub).calledOnceWith(50, 60)
            ).to.be.true;

            const pressStub = mockPage.keyboard.press as SinonStub;
            expect(pressStub.calledOnceWith("Enter")).to.be.true;

            const typeStub = mockPage.keyboard.type as SinonStub;
            expect(typeStub.callCount).to.equal(2);
            expect(typeStub.getCall(0).args[0]).to.equal("h");
            expect(typeStub.getCall(1).args[0]).to.equal("i");
        });

        it("should handle type_text_at with clearing and no enter", async () => {
            const command: Command = {
                name: "type_text_at",
                args: {
                    x: 50,
                    y: 60,
                    text: "hi",
                    press_enter: false,
                    clear_before_typing: true,
                },
            };

            const commandPromise = browserShell.runCommand(command);
            await clock.runAllAsync();
            await commandPromise;

            expect(
                (mockPage.mouse.click as SinonStub).calledOnceWith(50, 60)
            ).to.be.true;

            const downStub = mockPage.keyboard.down as SinonStub;
            expect(downStub.calledOnceWith("Control")).to.be.true;

            const upStub = mockPage.keyboard.up as SinonStub;
            expect(upStub.calledOnceWith("Control")).to.be.true;

            const pressStub = mockPage.keyboard.press as SinonStub;
            expect(pressStub.callCount).to.equal(2);
            expect(pressStub.getCall(0).args[0]).to.equal("a");
            expect(pressStub.getCall(1).args[0]).to.equal("Backspace");
            expect(pressStub.neverCalledWith("Enter")).to.be.true;

            const typeStub = mockPage.keyboard.type as SinonStub;
            expect(typeStub.callCount).to.equal(2);
            expect(typeStub.getCall(0).args[0]).to.equal("h");
            expect(typeStub.getCall(1).args[0]).to.equal("i");
        });

        it("should handle scroll_at", async () => {
            const command: Command = {
                name: "scroll_at",
                args: { x: 100, y: 200, direction: "up", magnitude: 50 },
            };
            await browserShell.runCommand(command);
            expect((mockPage.mouse.move as SinonStub).calledOnceWith(100, 200)).to.be
                .true;
            expect(
                (mockPage.mouse.wheel as SinonStub).calledOnceWith({
                    deltaY: -50,
                    deltaX: 0,
                })
            ).to.be.true;
        });

        it("should handle drag_and_drop", async () => {
            const command: Command = {
                name: "drag_and_drop",
                args: { x: 10, y: 20, destination_x: 30, destination_y: 40 },
            };
            await browserShell.runCommand(command);
            expect((mockPage.mouse.move as SinonStub).calledWith(10, 20)).to.be.true;
            expect((mockPage.mouse.down as SinonStub).calledOnce).to.be.true;
            expect((mockPage.mouse.move as SinonStub).calledWith(30, 40)).to.be.true;
            expect((mockPage.mouse.up as SinonStub).calledOnce).to.be.true;
        });

        it("should handle scroll_document (down)", async () => {
            const command: Command = {
                name: "scroll_document",
                args: { direction: "down" },
            };
            await browserShell.runCommand(command);
            expect(
                (mockPage.keyboard.press as SinonStub).calledOnceWith("PageDown")
            ).to.be.true;
        });

        it("should handle scroll_document (up)", async () => {
            const command: Command = {
                name: "scroll_document",
                args: { direction: "up" },
            };
            await browserShell.runCommand(command);
            expect(
                (mockPage.keyboard.press as SinonStub).calledOnceWith("PageUp")
            ).to.be.true;
        });
        it("should handle scroll_document (left)", async () => {
            const command: Command = {
                name: "scroll_document",
                args: { direction: "left" },
            };
            // Set viewport width to simulate left scroll
            (mockPage.viewport as SinonStub).returns({ width: 1000, height: 1000 });
            await browserShell.runCommand(command);
            expect(
                (mockPage.mouse.wheel as SinonStub).calledOnceWith({
                    deltaX: -500,
                })
            ).to.be.true;
        });

        it("should handle scroll_document (right)", async () => {
            const command: Command = {
                name: "scroll_document",
                args: { direction: "right" },
            };
            // Set viewport width to simulate right scroll
            (mockPage.viewport as SinonStub).returns({ width: 1000, height: 1000 });
            await browserShell.runCommand(command);
            expect(
                (mockPage.mouse.wheel as SinonStub).calledOnceWith({
                    deltaX: 500,
                })
            ).to.be.true;
        });

        it("should handle wait_5_seconds", async () => {
            const command: Command = { name: "wait_5_seconds" };
            const promise = browserShell.runCommand(command);
            // Check that it's not resolved too early
            await clock.tickAsync(4999);
            // A way to check if promise is still pending (specific to test runner or add a flag)
            // For simplicity, we'll just advance time fully and await.
            await clock.tickAsync(1); // Total 5000ms
            await promise; // ensure it resolves
        });

        it("should handle go_back", async () => {
            const command: Command = { name: "go_back" };
            await browserShell.runCommand(command);
            expect(
                (mockPage.waitForNavigation as SinonStub).calledOnceWith({
                    timeout: 5000,
                })
            ).to.be.true;
            expect((mockPage.goBack as SinonStub).calledOnce).to.be.true;
        });

        it("should handle go_forward", async () => {
            const command: Command = { name: "go_forward" };
            await browserShell.runCommand(command);
            expect(
                (mockPage.waitForNavigation as SinonStub).calledOnceWith({
                    timeout: 5000,
                })
            ).to.be.true;
            expect((mockPage.goForward as SinonStub).calledOnce).to.be.true;
        });

        it("should handle search (goes to google)", async () => {
            const command: Command = { name: "search" };
            await browserShell.runCommand(command);
            expect(
                (mockPage.goto as SinonStub).calledOnceWith("https://www.google.com")
            ).to.be.true;
        });

        it("should handle navigate", async () => {
            const command: Command = {
                name: "navigate",
                args: { url: "http://example.com" },
            };
            await browserShell.runCommand(command);
            expect(
                (mockPage.waitForNavigation as SinonStub).calledOnceWith({
                    timeout: 5000,
                })
            ).to.be.true;
            expect((mockPage.goto as SinonStub).calledOnceWith("http://example.com"))
                .to.be.true;
        });

        it("should handle key_combination with multiple keys", async () => {
            const command: Command = {
                name: "key_combination",
                args: { keys: "Control+Shift" },
            };
            await browserShell.runCommand(command);

            const expectedKeys: KeyInput[] = ["Control", "Shift"];

            expect((mockPage.keyboard.down as SinonStub).callCount).to.equal(
                expectedKeys.length
            );
            expect((mockPage.keyboard.up as SinonStub).callCount).to.equal(
                expectedKeys.length
            );

            for (let i = 0; i < expectedKeys.length; i++) {
                expect(
                    (mockPage.keyboard.down as SinonStub).getCall(i).args[0]
                ).to.equal(expectedKeys[i]);
                expect((mockPage.keyboard.up as SinonStub).getCall(i).args[0]).to.equal(
                    expectedKeys[i]
                );
            }
        });

        it("should handle key_combination formatting for mixed case and single char keys", async () => {
            const command: Command = {
                name: "key_combination",
                args: { keys: "alt+t+ENTER" },
            };
            // Expected formatting: 'alt' -> 'Alt', 't' -> 't', 'ENTER' -> 'Enter'
            const expectedFormattedKeys: KeyInput[] = ["Alt", "t", "Enter"];
            await browserShell.runCommand(command);

            expect((mockPage.keyboard.down as SinonStub).callCount).to.equal(
                expectedFormattedKeys.length
            );
            expectedFormattedKeys.forEach((key, index) => {
                expect(
                    (mockPage.keyboard.down as SinonStub).getCall(index).args[0]
                ).to.equal(key);
            });
            expect((mockPage.keyboard.up as SinonStub).callCount).to.equal(
                expectedFormattedKeys.length
            );
            expectedFormattedKeys.forEach((key, index) => {
                expect(
                    (mockPage.keyboard.up as SinonStub).getCall(index).args[0]
                ).to.equal(key);
            });
        });
    });

    describe("runCommand (headful mode delegation)", () => {
        beforeEach(() => {
            browserShell = new BrowserShell(mockBrowser, mockPage, false); // headless = false
            // For testing delegation, we replace the real OsShell with our mock instance.
            browserShell.headfulShell = mockOsShellInstance;
        });

        const headfulCommandTests: {
            command: Command;
            puppeteerMocksNotCalled: SinonStub[];
        }[] = [
            { name: "click_at", args: { x: 10, y: 20 } },
            { name: "hover_at", args: { x: 10, y: 20 } },
            { name: "type_text_at", args: { x: 10, y: 20, text: "test" } },
            { name: "key_combination", args: { keys: "Control+c" } },
        ].map((cmdArgs) => ({
            command: cmdArgs as Command,
            puppeteerMocksNotCalled: (() => {
                switch (cmdArgs.name) {
                    case "click_at":
                        return [mockPage.mouse.click as SinonStub];
                    case "hover_at":
                        return [mockPage.mouse.move as SinonStub];
                    case "type_text_at":
                        return [
                            mockPage.mouse.click as SinonStub,
                            mockPage.keyboard.type as SinonStub,
                            mockPage.keyboard.press as SinonStub,
                        ];
                    case "key_combination":
                        return [
                            mockPage.keyboard.down as SinonStub,
                            mockPage.keyboard.up as SinonStub,
                        ];
                    default:
                        return [];
                }
            })(),
        }));

        headfulCommandTests.forEach(({ command, puppeteerMocksNotCalled }) => {
            it(`should delegate ${command.name} to OsShell and not call page methods`, async () => {
                await browserShell.runCommand(command);
                expect(osShellRunCommandStub.calledOnceWith(command)).to.be.true;
                puppeteerMocksNotCalled.forEach((mockMethod) => {
                    expect(mockMethod.called).to.be.false;
                });
            });
        });

        it("should NOT delegate non-headful commands (e.g., navigate) to OsShell even in headful mode", async () => {
            const command: Command = {
                name: "navigate",
                args: { url: "http://notashellcommand.com" },
            };
            await browserShell.runCommand(command);
            expect(osShellRunCommandStub.notCalled).to.be.true;
            expect((mockPage.goto as SinonStub).calledOnceWith(command.args.url)).to
                .be.true;
        });

        it("should still handle scroll_document via puppeteer in headful mode (as it is not in HEADFUL_COMMANDS)", async () => {
            const command: Command = {
                name: "scroll_document",
                args: { direction: "down" },
            };
            await browserShell.runCommand(command);
            expect(osShellRunCommandStub.notCalled).to.be.true;
            expect(
                (mockPage.keyboard.press as SinonStub).calledOnceWith("PageDown")
            ).to.be.true;
        });
    });

    describe("currentUrl", () => {
        it("should return the current page URL from page.url()", () => {
            browserShell = new BrowserShell(mockBrowser, mockPage, true);
            (mockPage.url as SinonStub).returns("http://test.com/page");
            const url = browserShell.currentUrl();
            expect(url).to.equal("http://test.com/page");
            expect((mockPage.url as SinonStub).calledOnce).to.be.true;
        });
    });

    describe("screenshot", () => {
        describe("headless mode", () => {
            beforeEach(() => {
                browserShell = new BrowserShell(mockBrowser, mockPage, true); // headless = true
            });

            it("should take a screenshot using puppeteer page.screenshot", async () => {
                (mockPage.screenshot as SinonStub).resolves("base64data_headless_page");
                const screenshotData = await browserShell.screenshot();
                expect(screenshotData).to.equal("base64data_headless_page");
                expect(
                    (mockPage.screenshot as SinonStub).calledOnceWith({
                        encoding: "base64",
                        type: "png",
                        captureBeyondViewport: false,
                    })
                ).to.be.true;
                // Ensure OsShell's screenshot was not involved if headfulShell is undefined (which it is in headless)
                // This check is implicitly covered by headfulShell being undefined.
            });
        });

        describe("headful mode", () => {
            beforeEach(() => {
                browserShell = new BrowserShell(mockBrowser, mockPage, false); // headless = false
                browserShell.headfulShell = mockOsShellInstance; // Inject mock for testing delegation
            });

            it("should delegate screenshot to OsShell", async () => {
                osShellScreenshotStub.resolves("base64data_headful_os_specific");
                const screenshotData = await browserShell.screenshot();
                expect(screenshotData).to.equal("base64data_headful_os_specific");
                expect(osShellScreenshotStub.calledOnce).to.be.true;
                expect((mockPage.screenshot as SinonStub).notCalled).to.be.true;
            });
        });
    });
});
