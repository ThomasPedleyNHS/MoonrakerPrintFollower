"""Executable qml dashboard layout contracts."""
from tests import qml_engine_support as harness

class StatusColumnGeometryTests(harness.StatusColumnGeometryTests):
    def test_the_status_column_tracks_the_pane_viewport(self):
        # The regression: without an explicit viewport-relative width
        # the column sat at its own implicit width (301 px) inside a
        # 238 px pane — the sections painted past the pane's edge at
        # every size and never filled it. The widths stay above the
        # status pane's fold: folded, the column is the strip. The
        # mount is windowed because the narrow-window rule needs a
        # second layout pass to settle: a windowless mount stops on
        # the pass whose camera still reads the squeezed pane (the
        # harness note on _settle).
        for width in (760, 900):
            monitor, _window = self.mount_window("MoonrakerMonitor.qml", width, 760)
            flick = self.find(monitor, "moonrakerStatusFlick")
            content = self.find(monitor, "moonrakerStatusContent")
            self.assertFalse(monitor.property("statusCollapsed"),
                             "the pane folded at %d" % width)
            self.assertGreater(flick.width(), 100, "the status pane did not lay out")
            self.assertAlmostEqual(content.width(), flick.width() - 14, delta=0.5)
        self.assertEqual(monitor.width(), 900)

    def test_the_sections_fill_the_column_once_it_is_wide(self):
        monitor, _window = self.mount_window("MoonrakerMonitor.qml", 900, 760)
        content = self.find(monitor, "moonrakerStatusContent")
        sections = [child for child in content.childItems() if child.isVisible() and child.width() > 0]
        # Objects moved to the controls pane (4.6.0): two sections
        # render unconditionally here without live data.
        self.assertGreaterEqual(len(sections), 2)
        for section in sections:
            self.assertAlmostEqual(section.width(), content.width(), delta=0.5)

    def test_the_column_never_keeps_its_own_implicit_width(self):
        # The narrow viewport is the crisp case: the column is NARROWER
        # than the content it holds, which only happens when the width
        # tracks the flickable. Below the pane's fold a narrow viewport
        # is the collapsed pane's readout strip.
        for width in (520, 560):
            monitor = self.mount_monitor(width)
            flick = self.find(monitor, "moonrakerStatusFlick")
            content = self.find(monitor, "moonrakerStatusContent")
            self.assertAlmostEqual(content.width(), flick.width() - 14, delta=0.5)
            # A positioner derives implicitWidth from its explicitly sized
            # children; the contract is that none escape the viewport.
            for section in content.childItems():
                if section.width() > 0:
                    self.assertAlmostEqual(section.width(), content.width(), delta=0.5)


class ConsoleInputRowTests(harness.ConsoleInputRowTests):
    def test_the_input_keeps_the_buttons_in_their_own_cells(self):
        # The 5.11/5.12 sweep: the field's hit region covered Send and
        # Clear, so the presses aimed at them landed on the field. The
        # field shrinks and clips inside its own cell; the buttons hold
        # theirs at every pane width.
        for width in (1600, 900, 640):
            monitor = self.mount_monitor(width)
            field = self.rect(self.find(monitor, "moonrakerConsoleInput"), monitor)
            send = self.rect(self.find(monitor, "moonrakerConsoleSend"), monitor)
            clear = self.rect(self.find(monitor, "moonrakerConsoleClear"), monitor)
            self.assertLessEqual(field.right(), send.left() + 0.5, "field covers Send at %d" % width)
            self.assertLessEqual(send.right(), clear.left() + 0.5, "Send covers Clear at %d" % width)
            self.assertGreater(send.width(), 0.0)
            self.assertGreater(clear.width(), 0.0)


class PaneGutterTests(harness.PaneGutterTests):
    def test_the_monitor_panes_keep_the_constant_right_gutter(self):
        monitor, window = self.mount_window("MoonrakerMonitor.qml", 1600, 760)
        for width in (1600, 1200, 900, 700, 520):
            self.resize_window(monitor, window, width, 760)
            self.assert_gutter(self.find(monitor, "infoPanel"),
                               self.find(monitor, "moonrakerInfoContent"),
                               "information@%d" % width)
            self.assert_gutter(self.find(monitor, "statusPanel"),
                               self.find(monitor, "moonrakerStatusContent"),
                               "status@%d" % width)

    def test_the_controls_pane_keeps_the_same_gutter(self):
        for width in (1600, 900):
            dashboard, window = self.mount_window("MoonrakerMonitorDashboard.qml", width, 760)
            self.assert_gutter(self.find(dashboard, "moonrakerControlsPane"),
                               self.find(dashboard, "moonrakerControlsContent"),
                               "controls@%d" % width)


class PauseRowRoleTests(harness.PauseRowRoleTests):
    def test_rows_without_a_state_or_eta_keep_the_model_roles(self):
        card = self.mount("MoonrakerPreviewCard.qml")
        card.setProperty("pauseAtLayerItems", self.SPARSE)
        self.pump()
        self.assert_roles_are_concrete(card)
        self.assertEqual(self.new_messages(), [])

    def test_rows_without_a_state_or_eta_render_their_lines(self):
        card = self.pause_card(self.SPARSE)
        self.assert_roles_are_concrete(card)
        self.assertEqual(self.pause_rows(card),
                         ["End of layer 5", "End of layer 7", "End of layer 9"])
        self.assertEqual([message for message in self.new_messages() if "ReferenceError" in message], [])

    def test_mixed_rows_render_the_state_and_the_eta(self):
        card = self.pause_card(self.MIXED)
        self.assert_roles_are_concrete(card)
        self.assertEqual(self.pause_rows(card), [
            "End of layer 5",
            "End of layer 7 · in 00:02:00",
            "End of layer 9 — passed",
            "End of layer 12",
        ])
        self.assertEqual([message for message in self.new_messages() if "ReferenceError" in message], [])


class StripVerdictRefreshTests(harness.StripVerdictRefreshTests):
    def test_a_verdict_only_change_refreshes_the_strip(self):
        # The strip watched the block, the
        # staleness and the ETA but not the verdicts, so a verdict that
        # changed alone left the outgoing copy and the dead button.
        card = self.verdict_card()
        slot = self.find(card, "moonrakerStripSlot")
        button = self.find(card, "moonrakerStripPauseButton")
        self.assertEqual(slot.property("text"), "Print is not printing")
        self.assertFalse(button.property("enabled"))
        card.setProperty("stripCanPause", True)  # block and ETA untouched
        self.pump()
        self.assertEqual(slot.property("text"), "00:18:42")
        self.assertTrue(button.property("enabled"))


class TuningResetTests(harness.TuningResetTests):
    def test_each_reset_button_commands_its_factor_to_100(self):
        from PyQt6.QtTest import QTest
        from PyQt6.QtCore import Qt

        class ModelDouble(harness.QObject):
            def __init__(self):
                super().__init__()
                self.calls = []

            @harness.pyqtSlot(int)
            def setSpeedFactor(self, percent):
                self.calls.append(("speed", percent))

            @harness.pyqtSlot(int)
            def setFlowFactor(self, percent):
                self.calls.append(("flow", percent))

            @harness.pyqtSlot(int)
            def previewSpeedFactor(self, percent):
                pass

            @harness.pyqtSlot(int)
            def previewFlowFactor(self, percent):
                pass

            @harness.pyqtProperty("QVariant")
            def sectionExpandedMap(self):
                return {}

            @harness.pyqtProperty(bool)
            def controlsLocked(self):
                return False

            @harness.pyqtProperty(bool)
            def monitorConnected(self):
                return True

        section = self.mount("TuningSection.qml")
        window = harness.QQuickWindow()
        window.resize(520, 400)
        section.setParentItem(window.contentItem())
        window.show()
        self.addCleanup(window.deleteLater)
        model = ModelDouble()
        section.setProperty("printerModel", model)
        self.pump(30)
        # A real click at each button's centre (the newer Qt's clicked
        # signal carries a QQuickMouseEvent PyQt cannot introspect, so
        # the signal is not accessible from Python — the event path is
        # the honest one anyway).
        for name in ("moonrakerTuningSpeedReset", "moonrakerTuningFlowReset"):
            button = self.find(section, name)
            center = button.mapToScene(harness.QPointF(button.width() / 2, button.height() / 2)).toPoint()
            QTest.mouseClick(window, Qt.MouseButton.LeftButton, pos=center)
        self.pump(30)
        self.assertIn(("speed", 100), model.calls)
        self.assertIn(("flow", 100), model.calls)


class TuningResetConvergenceTests(harness.TuningResetConvergenceTests):
    def test_the_flow_slider_reads_100_after_the_reset_converges(self):
        from PyQt6.QtTest import QTest
        from PyQt6.QtCore import Qt

        class ModelDouble(harness.QObject):
            flowFactorPercentChanged = harness.pyqtSignal()

            def __init__(self):
                super().__init__()
                self._flow = 137
                self.calls = []

            @harness.pyqtProperty(int)
            def speedFactorPercent(self):
                return 100

            @harness.pyqtProperty(int, notify=flowFactorPercentChanged)
            def flowFactorPercent(self):
                return self._flow

            def confirm(self, value):
                self._flow = value
                self.flowFactorPercentChanged.emit()

            @harness.pyqtSlot(int)
            def setFlowFactor(self, percent):
                self.calls.append(("flow", percent))

            @harness.pyqtSlot(int)
            def previewFlowFactor(self, percent):
                pass

            @harness.pyqtProperty("QVariant")
            def sectionExpandedMap(self):
                return {}

            @harness.pyqtProperty(bool)
            def controlsLocked(self):
                return False

            @harness.pyqtProperty(bool)
            def monitorConnected(self):
                return True

        section = self.mount("TuningSection.qml")
        window = harness.QQuickWindow()
        window.resize(520, 400)
        section.setParentItem(window.contentItem())
        window.show()
        self.addCleanup(window.deleteLater)
        model = ModelDouble()
        section.setProperty("printerModel", model)
        self.pump(30)
        button = self.find(section, "moonrakerTuningFlowReset")
        slider = None
        for item in button.parentItem().childItems():
            if "OutlineSlider" in item.metaObject().className():
                slider = item
                break
        self.assertIsNotNone(slider, "the flow slider did not build")
        self.assertEqual(slider.property("value"), 137)
        # A prior user interaction writes the slider's value directly
        # (the drag path) — under the old binding that destroyed the
        # model link and the reset's 100 could never reach the handle.
        slider.setProperty("value", 200)
        self.pump(30)
        center = button.mapToScene(harness.QPointF(button.width() / 2, button.height() / 2)).toPoint()
        QTest.mouseClick(window, Qt.MouseButton.LeftButton, pos=center)
        self.pump(30)
        self.assertIn(("flow", 100), model.calls)
        model.confirm(100)  # the printer's polled confirmation
        self.pump(30)
        self.assertEqual(slider.property("value"), 100,
                         "the slider must read the confirmed 100, not the to-clamp")






class DynamicPaneStackTests(harness.RealEngineTestCase):
    def test_section_visibility_and_height_changes_settle_without_layout_feedback(self):
        dashboard, window = self.mount_window("MoonrakerMonitorDashboard.qml", 1840, 900)
        self._pump_ms(100)
        columns = [self.find(dashboard, name) for name in
                   ("moonrakerStatusContent", "moonrakerControlsContent")]
        start = len(harness._APPLICATION["messages"])
        for column in columns:
            sections = [child for child in column.childItems() if child.width() > 0]
            for section in sections:
                section.setVisible(False)
                self._pump_ms(20)
                section.setVisible(True)
                self._pump_ms(20)
                self.assertAlmostEqual(section.width(), column.width(), delta=0.5)
            self._pump_ms(50)
            shown = sorted((child for child in sections if child.isVisible()), key=lambda child: child.y())
            for previous, following in zip(shown, shown[1:], strict=False):
                self.assertGreaterEqual(following.y() + .5, previous.y() + previous.height())
        self.assertFalse([line for line in harness._APPLICATION["messages"][start:]
                          if "polish loop" in line.lower() or "binding loop" in line.lower()])


class FileManagerOpenBindingTests(harness.RealEngineTestCase):
    def test_fetch_publish_does_not_reenter_the_open_binding(self):
        from tools.capture_filemanager import FileManagerModelStub

        class PublishingModel(FileManagerModelStub):
            fileManagerChanged = harness.pyqtSignal()

            def __init__(self):
                super().__init__()
                self.opened = False
                self.fetches = 0

            @harness.pyqtProperty(bool, notify=fileManagerChanged)
            def fileManagerOpen(self):
                return self.opened

            @harness.pyqtSlot()
            def openFileManager(self):
                self.fetches += 1
                self.fileManagerChanged.emit()

            def publish(self, opened):
                self.opened = opened
                self.fileManagerChanged.emit()

        model = PublishingModel()
        context = self.engine.rootContext()
        context.setContextProperty("openingPrinter", model)
        self.addCleanup(context.setContextProperty, "openingPrinter", None)
        component = harness.QQmlComponent(self.engine)
        component.setData(b"import QtQuick 2.15; Item { width: 900; height: 600; "
                          b"property bool fileManagerOpen: openingPrinter.fileManagerOpen; "
                          b"FileManager { anchors.fill: parent; open: parent.fileManagerOpen; "
                          b"printerModel: openingPrinter } }",
                          harness.QUrl.fromLocalFile(str(harness.ROOT / "plugins" / "OpenProbe.qml")))
        document = component.create()
        self.assertIsNotNone(document, harness.qml_error_report(component))
        window = harness.QQuickWindow()
        window.resize(900, 600)
        document.setParentItem(window.contentItem())
        self.addCleanup(self._destroy_window, document, window)
        window.show()
        self.pump(30)
        start = len(harness._APPLICATION["messages"])
        model.publish(True)
        self._pump_ms(50)
        self.assertEqual(model.fetches, 1)
        model.publish(False)
        self._pump_ms(30)
        model.publish(True)
        self._pump_ms(50)
        self.assertEqual(model.fetches, 2)
        self.assertFalse([line for line in harness._APPLICATION["messages"][start:]
                          if "binding loop" in line.lower()])


class SectionContentSizingTests(harness.RealEngineTestCase):
    def check_section(self, filename, section_id, models):
        section = self.mount(filename)
        window = harness.QQuickWindow()
        window.resize(500, 900)
        section.setParentItem(window.contentItem())
        self.addCleanup(window.deleteLater)
        window.show()
        header = section.childItems()[0]
        start = len(harness._APPLICATION["messages"])
        for width in (383, 240, 359):
            section.setWidth(width)
            for model in models:
                for expanded in (True, False, True):
                    section.setProperty("printerModel", dict(model, sectionExpandedMap={section_id: expanded}))
                    self._pump_ms(35)
                    self.assertAlmostEqual(header.width(), width, delta=.5)
                    if not expanded:
                        self.assertAlmostEqual(section.height(), header.height(), delta=.5)
                    else:
                        body = section.childItems()[1]
                        if body.isVisible():
                            self.assertGreater(section.height(), header.height())
                            self.assertAlmostEqual(section.height(), body.y() + body.height()
                                                   + section.property("verticalMargin"), delta=.5)
                            self.assertLessEqual(body.x() + body.width(), width)
        self.assertFalse([line for line in harness._APPLICATION["messages"][start:]
                          if "polish loop" in line.lower() or "binding loop" in line.lower()])

    def test_profiles_arrive_change_and_disappear_without_height_feedback(self):
        base = dict(controlsLocked=False, monitorConnected=True, canApplyTemperaturePreset=True,
                    sectionReason="", sectionReasonDetail="", printActive=False)
        models = [dict(base, temperaturePresetItems=rows) for rows in
                  ([], [{"active": False, "name": "PLA", "index": 0}],
                   [{"active": True, "name": "A longer named profile", "index": 0},
                    {"active": False, "name": "ABS", "index": 1}], [])]
        self.check_section("ProfilesSection.qml", "profiles", models)

    def test_job_telemetry_and_download_rows_keep_the_section_height_content_driven(self):
        base = dict(actionStatus="", actionTimestamp="", filamentRemaining="—", filamentUsed="—",
                    improveEtaPhase="", improveEtaProgress=0, improvingEta=False,
                    monitorAccelLimit="—", monitorConnected=True, monitorElapsed="00:00:01",
                    monitorEta="—", monitorEtaBasis="", monitorFilename="test.gcode", monitorFinish="—",
                    monitorFlow="100%", monitorFlowDiameter="1.75 mm", monitorFlowRate="—",
                    monitorLayer="—", monitorLayerProgress=-1, monitorLayerSource="", monitorMessage="",
                    monitorPositionX="—", monitorPositionY="—", monitorPositionZ="—", monitorProgress=0,
                    monitorSpeed="100%", monitorState="Printing", monitorVelocity="—", nextPauseBaked=False,
                    nextPauseEta="", nextPauseFraction=-1, platePassFraction=-1, printActive=True,
                    printIndexReady=False)
        self.check_section("JobSection.qml", "job", [base, dict(base, improvingEta=True,
                           improveEtaProgress=.5), dict(base, printIndexReady=True, monitorLayer="2 / 100",
                           monitorLayerProgress=.3, monitorEta="00:10:00", monitorPositionX="10.0",
                           monitorPositionY="20.0", monitorPositionZ=".4")])
