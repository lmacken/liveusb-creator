import QtQuick 2.0
import QtQuick.Controls 1.2
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.1
import QtQuick.Window 2.0

Dialog {
    id: root
    title: "Write Fedora Workstation to USB"

    contentItem: Rectangle {
        ToolBar {
            id: dialogToolBar
            height: 48

            Button {
                anchors {
                    left: parent.left
                    top: parent.top
                    bottom: parent.bottom
                    margins: 6
                }
                width: implicitWidth * 1.2
                text: "Cancel"
                onClicked: root.close()
            }
            Text {
                anchors.centerIn: parent
                text: "Write Fedora Workstation to USB"
            }
            Button {
                anchors {
                    right: parent.right
                    top: parent.top
                    bottom: parent.bottom
                    margins: 6
                }
                width: implicitWidth * 1.2
                enabled: false
                text: "Write to disk"
            }
        }
        color: palette.window
        implicitWidth: 600
        implicitHeight: 300
        ColumnLayout {
            id: layout
            spacing: 24
            anchors {
                top: dialogToolBar.bottom
                left: parent.left
                right: parent.right
                bottom: parent.bottom
                topMargin: 48
                leftMargin: 64
                rightMargin: anchors.leftMargin
                bottomMargin: anchors.topMargin
            }

            Text {
                Layout.fillWidth: true
                width: layout.width
                wrapMode: Text.WordWrap
                text: "Writing the image of Fedora Workstation will delete everything that's currently on the drive."
            }

            ColumnLayout {
                Text {
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignHCenter
                    text: "Downloading (895MB left)"
                }
                ProgressBar {
                    Layout.fillWidth: true
                    value: 0.2
                }
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignCenter
                spacing: 32
                Image {
                    source: "http://upload.wikimedia.org/wikipedia/commons/3/3f/Fedora_logo.svg"
                    sourceSize.width: 64
                    sourceSize.height: 64
                    fillMode: Image.PreserveAspectFit
                }
                Arrow {

                }
                ComboBox {
                    model: ListModel {
                        ListElement { text: "SanDisk Cruzer 2.0 GB Drive"; device:"sdj1" }
                    }
                }
            }
        }
    }
}
