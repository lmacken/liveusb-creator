import QtQuick 2.4
import QtQuick.Controls 1.3
import QtQuick.Controls.Styles 1.4
import QtQuick.Layouts 1.1

Item {
    id: popover
    z: -1
    property bool open: false
    visible: opacity > 0.0
    opacity: open ? 1.0 : 0.0
    Behavior on opacity { NumberAnimation { duration: 150 } }

    height: popoverLayout.height + $(12)
    width: popoverLayout.width + $(12)

    Rectangle {
        anchors.fill: popoverLayout
        anchors.margins: - $(12)
        color: palette.window
        antialiasing: true
        border {
            width: 1
            color: "#b1b1b1"
        }
        radius: $(6)
        Rectangle {
            z: -1
            y: -$(6.5) - 1
            antialiasing: true
            border.color: "#b1b1b1"
            border.width: 1
            color: palette.window
            anchors.horizontalCenter: parent.horizontalCenter
            width: $(14)
            height: $(14)
            rotation: 45
        }
        Rectangle {
            color: palette.window
            y: -$(6.5) + 1
            anchors.horizontalCenter: parent.horizontalCenter
            width: $(14)
            height: $(14)
            rotation: 45
        }
    }

    ColumnLayout {
        id: popoverLayout
        spacing: $(9)
        ExclusiveGroup {
            id: archEG
        }
        // TODO move the content outside
        Repeater {
            model: liveUSBData.currentImage.arch
            AdwaitaRadioButton {
                text: modelData
                Layout.alignment: Qt.AlignVCenter
                exclusiveGroup: archEG
                checked: liveUSBData.releaseProxyModel.archFilter == modelData
                onCheckedChanged: {
                    if (checked && liveUSBData.releaseProxyModel.archFilter != modelData)
                        liveUSBData.releaseProxyModel.archFilter = modelData
                }
            }
        }
    }
}
