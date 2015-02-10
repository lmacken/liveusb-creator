import QtQuick 2.0
import QtQuick.Controls 1.2
import QtQuick.Layouts 1.1

Item {
    id: root

    signal stepForward

    ScrollView {
        anchors {
            fill: parent
            leftMargin: anchors.rightMargin
        }

        contentItem: Item {
            y: 48
            x: 64
            width: root.width - 2 * 64
            height: childrenRect.height + 64 + 32

            ColumnLayout {
                width: parent.width
                spacing: 32
                RowLayout {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    spacing: 32
                    Layout.alignment: Qt.AlignLeft
                    IndicatedImage {
                        id: iconRect
                        source: "http://upload.wikimedia.org/wikipedia/commons/3/3f/Fedora_logo.svg"
                        sourceSize.width: 64
                        sourceSize.height: 64
                        fillMode: Image.PreserveAspectFit
                    }

                    ColumnLayout {
                        Layout.alignment: Qt.AlignLeft
                        spacing: 8
                        Text {
                            text: "Fedora Workstation 21"
                        }
                        RowLayout {
                            Text {
                                Layout.fillWidth: true
                                anchors.left: parent.left
                                text: "64bit"
                                color: "gray"
                            }
                            Text {
                                anchors.right: parent.right
                                text: "953MB"
                                color: "gray"
                            }
                        }
                    }
                }
                Text {
                    Layout.fillWidth: true
                    width: Layout.width
                    wrapMode: Text.WordWrap
                    text: "Lorem ipsum, quia dolor sit, amet, consectetur, adipisci velit, sed quia non numquam eius modi tempora incidunt, ut labore et dolore magnam aliquam quaerat voluptatem. Ut enim ad minima veniam, quis nostrum exercitationem ullam corporis suscipit laboriosam, nisi ut aliquid ex ea commodi consequatur? Quis autem vel eum iure reprehenderit, qui in ea voluptate velit esse, quam nihil molestiae consequatur, vel illum, qui dolorem eum fugiat, quo voluptas nulla pariatur?"
                    font.pointSize: 9
                }
                RowLayout {
                    spacing: 16
                    ColumnLayout {
                        Layout.fillWidth: true
                        Text {
                            Layout.fillWidth: true
                            text: "ISO format image for Intel-compatible PCs (64-bit)"
                            font.pointSize: 8
                            color: "gray"
                        }
                        Text {
                            Layout.fillWidth: true
                            text: "Released on December 21st 2014"
                            font.pointSize: 8
                            color: "gray"
                        }
                    }
                    AdwaitaButton {
                        text: "Write to USB disk"
                        onClicked: dialog.visible = true
                    }
                    AdwaitaButton {
                        enabled: false
                        text: "Boot with Boxes"
                    }
                }
                IndicatedImage {
                    Layout.fillWidth: true
                    fillMode: Image.PreserveAspectFit
                    source: "http://fedora.cz/wp-content/uploads/2013/12/fedora-20-gnome-10.png"
                    sourceSize.width: width
                }
            }
        }
    }
    DownloadDialog {
        id: dialog
    }
}

