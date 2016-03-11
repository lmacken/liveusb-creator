import QtQuick 2.4
import QtQuick.Controls 1.3
import QtQuick.Controls.Styles 1.4
import QtQuick.Window 2.2
import QtGraphicalEffects 1.0
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.1

Dialog {
    id: root
    title: liveUSBData.driveToRestore ? qsTranslate("", "Restore %1?").arg(liveUSBData.driveToRestore.text) : ""

    property int state: 0

    contentItem : Rectangle {
        implicitWidth: $(480)
        implicitHeight: textItem.height + buttonItem.height + $(48)
        height: textItem.height + buttonItem.height + $(48)
        color: palette.window
        Item {
            id: wrapper
            anchors.fill: parent
            anchors.margins: $(18)
            Row {
                id: textItem
                spacing: $(36)
                x: root.state == 0 ? 0 : root.state == 1 ? - (parent.width + $(36)) : - (2 * parent.width + $(72))
                height: progress.height > warningText.height ? progress.height : warningText.height
                Behavior on x {
                    NumberAnimation {
                        duration: 300
                        easing.type: Easing.OutExpo
                    }
                }
                Text {
                    id: warningText
                    width: wrapper.width
                    text: qsTranslate("", "<p align=\"justify\">To reclaim all space available on the drive, it has to be restored to factory settings. The live system and all saved data will be deleted.</p><p>Do you want to continue?</p>")
                    textFormat: Text.RichText
                    wrapMode: Text.WrapAtWordBoundaryOrAnywhere
                }
                ColumnLayout {
                    id: progress
                    width: wrapper.width
                    spacing: $(12)
                    Item {
                        width: 1; height: 1
                    }

                    AdwaitaBusyIndicator {
                        id: progressIndicator
                        width: $(256)
                        Layout.alignment: Qt.AlignHCenter
                    }

                    Text {
                        Layout.alignment: Qt.AlignHCenter
                        Layout.fillWidth: true
                        wrapMode: Text.WrapAtWordBoundaryOrAnywhere
                        text: qsTranslate("", "<p justify=\"align\">Please wait while Fedora Media Writer restores your portable drive.</p>")
                    }
                }
                ColumnLayout {
                    width: wrapper.width
                    CheckMark {
                        Layout.alignment: Qt.AlignHCenter
                    }
                    Text {
                        Layout.alignment: Qt.AlignHCenter
                        text: "Your drive was successfully restored!"
                    }
                }
            }

            Row {
                id: buttonItem
                anchors.bottom: parent.bottom
                anchors.right: parent.right
                spacing: $(12)
                AdwaitaButton {
                    text: "Cancel"
                    enabled: root.state == 0
                    visible: root.state != 2
                    onClicked: root.visible = false
                }
                AdwaitaButton {
                    text: root.state == 2 ? "Close" : "Restore"
                    color: root.state == 2 ? "#628fcf" : "red"
                    textColor: "white"
                    //enabled: root.state != 1
                    onClicked: root.state = (root.state + 1) % 3
                }
            }
        }
    }
}
