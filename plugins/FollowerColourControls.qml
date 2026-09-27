import QtQuick 2.15
import QtQuick.Layouts 1.3
import UM 1.5 as UM
import Cura 1.1 as Cura
import "theme"
import "PreviewColours.js" as PreviewColours

ColumnLayout {
    id: root
    property var printerModel: null
    property var face: null
    property var scheme: face != null ? face.colourScheme : ({
            mode: 1
        })
    property int mode: scheme.mode === undefined ? 1 : scheme.mode
    property var limits: face != null ? face.colourRanges[PreviewColours.key(mode)] || [0, 0] : [0, 0]
    property string units: mode === 2 ? "mm/s" : (mode === 5 ? "mm³/s" : "mm")
    spacing: UM.Theme.getSize("thin_margin").height
    RowLayout {
        Layout.fillWidth: true
        UM.Label {
            text: "Colour scheme"
        }
        Cura.ComboBox {
            objectName: "moonrakerFollowerColourMode"
            Layout.preferredWidth: 210 * screenScaleFactor
            model: ["Material Colour", "Line type", "Speed", "Layer thickness", "Line thickness", "Flow rate"]
            currentIndex: root.mode
            onActivated: function (index) {
                if (root.printerModel != null)
                    root.printerModel.setFollowerColourMode(index);
            }
        }
        Item {
            Layout.fillWidth: true
        }
    }
    Flow {
        visible: root.mode === 0
        Layout.fillWidth: true
        spacing: UM.Theme.getSize("thin_margin").width
        Repeater {
            model: root.scheme.materials || []
            delegate: Row {
                spacing: 3 * screenScaleFactor
                Rectangle {
                    width: 12 * screenScaleFactor
                    height: 3 * screenScaleFactor
                    color: modelData
                    anchors.verticalCenter: parent.verticalCenter
                }
                UM.Label {
                    text: "Tool " + (index + 1)
                }
            }
        }
    }
    RowLayout {
        visible: root.mode >= 2
        Layout.fillWidth: true
        UM.Label {
            text: Number(root.limits[0]).toFixed(2) + " " + root.units
        }
        Row {
            Layout.fillWidth: true
            Layout.preferredHeight: 8 * screenScaleFactor
            Repeater {
                model: 64
                delegate: Rectangle {
                    width: parent.width / 64
                    height: parent.height
                    color: PreviewColours.gradient(root.mode, root.limits[0] + (root.limits[1] - root.limits[0]) * index / 63, root.limits)
                }
            }
        }
        UM.Label {
            text: Number(root.limits[1]).toFixed(2) + " " + root.units
        }
    }
    Row {
        visible: root.mode !== 1
        spacing: 4 * screenScaleFactor
        Rectangle {
            width: 12 * screenScaleFactor
            height: 2 * screenScaleFactor
            color: MoonrakerTheme.seriesDefault
            opacity: 0.55
            anchors.verticalCenter: parent.verticalCenter
        }
        UM.Label {
            text: "Layer ghost"
        }
    }
    Flow {
        Layout.fillWidth: true
        spacing: UM.Theme.getSize("thin_margin").width
        UM.Label {
            text: "Travels:"
        }
        Repeater {
            model: [
                {
                    name: "TRAVEL",
                    label: "Non retracted"
                },
                {
                    name: "TRAVEL_RETRACTING",
                    label: "Retracting"
                },
                {
                    name: "TRAVEL_RETRACTED",
                    label: "Retracted"
                },
                {
                    name: "TRAVEL_PRIMING",
                    label: "Priming"
                }
            ]
            delegate: Row {
                spacing: 3 * screenScaleFactor
                Rectangle {
                    width: 12 * screenScaleFactor
                    height: 1 * screenScaleFactor
                    color: root.face != null ? root.face.classColour(modelData.name) : MoonrakerTheme.plateTravel
                    anchors.verticalCenter: parent.verticalCenter
                }
                UM.Label {
                    text: modelData.label
                }
            }
        }
    }
}
