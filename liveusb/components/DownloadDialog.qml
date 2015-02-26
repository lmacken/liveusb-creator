import QtQuick 2.0
import QtQuick.Controls 1.2
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.1
import QtQuick.Window 2.0

Dialog {
    id: root
    title: "Write Fedora Workstation to USB"

    contentItem: Rectangle {
        color: palette.window
        implicitWidth: 600
        implicitHeight: 300
        ColumnLayout {
            id: layout
            spacing: 24
            anchors {
                fill: parent
                topMargin: 48
                leftMargin: 64
                rightMargin: anchors.leftMargin
                bottomMargin: anchors.topMargin * 2
            }

            Text {
                Layout.fillWidth: true
                width: layout.width
                wrapMode: Text.WordWrap
                text: "Writing the image of " + liveUSBData.currentImage.name +" will delete everything that's currently on the drive."
            }

            ColumnLayout {
                Text {
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignHCenter
                    property double leftSize: liveUSBData.currentImage.download.maxProgress - liveUSBData.currentImage.download.progress
                    property string leftStr: leftSize <= 0 ? "" :
                                             (leftSize < 1024) ? (leftSize + " B") :
                                             (leftSize < (1024 * 1024)) ? ((leftSize / 1024).toFixed(1) + " KB") :
                                             (leftSize < (1024 * 1024 * 1024)) ? ((leftSize / 1024 / 1024).toFixed(1) + " MB") :
                                             ((leftSize / 1024 / 1024 / 1024).toFixed(1) + " GB")
                    text: liveUSBData.currentImage.status + (liveUSBData.currentImage.download.maxProgress > 0 ? " (" + leftStr + " left)" : "")
                }
                Item {
                    Layout.fillWidth: true
                    height: childrenRect.height
                    AdwaitaProgressBar {
                        width: parent.width
                        value: liveUSBData.currentImage.download.running ? liveUSBData.currentImage.download.progress / liveUSBData.currentImage.download.maxProgress : 0
                        visible: !liveUSBData.currentImage.writer.running
                    }
                    AdwaitaProgressBar {
                        width: parent.width
                        value: liveUSBData.currentImage.writer.running ? liveUSBData.currentImage.writer.progress / liveUSBData.currentImage.writer.maxProgress : 0
                        visible: !liveUSBData.currentImage.download.running
                        progressColor: "red"
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignCenter
                spacing: 32
                IndicatedImage {
                    source: liveUSBData.currentImage.logo
                    sourceSize.width: 64
                    sourceSize.height: 64
                    fillMode: Image.PreserveAspectFit
                }
                Arrow {

                }
                AdwaitaComboBox {
                    Layout.preferredWidth: implicitWidth * 2
                    model: liveUSBData.usbDrives
                }
            }
        }
        Item {
            id: dialogToolBar
            height: 32
            anchors {
                left: parent.left
                right: parent.right
                bottom: parent.bottom
                bottomMargin: 24
                leftMargin: 16
                rightMargin: anchors.leftMargin
            }

            AdwaitaButton {
                id: cancelButton
                anchors {
                    right: acceptButton.left
                    top: parent.top
                    bottom: parent.bottom
                    rightMargin: 6
                }
                width: implicitWidth * 1.2
                text: "Cancel"
                onClicked: {
                    liveUSBData.currentImage.download.cancel()
                    root.close()
                }
            }
            AdwaitaButton {
                id: acceptButton
                anchors {
                    right: parent.right
                    top: parent.top
                    bottom: parent.bottom
                }
                color: "red"
                textColor: enabled ? "white" : palette.text
                width: implicitWidth * 1.2
                enabled: liveUSBData.currentImage.readyToWrite
                text: "Write to disk"
            }
        }
    }
}
