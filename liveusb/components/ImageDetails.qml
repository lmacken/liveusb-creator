import QtQuick 2.0
import QtQuick.Controls 1.2
import QtQuick.Controls.Styles 1.2
import QtQuick.Layouts 1.1

Item {
    id: root

    signal stepForward

    Rectangle {
        z: 2
        gradient: Gradient {
            GradientStop { position: 0.0; color: palette.window }
            GradientStop { position: 0.1; color: palette.window }
            GradientStop { position: 0.2; color: Qt.tint(palette.window, "transparent") }
            GradientStop { position: 1.0; color: "transparent" }
        }
        id: tools
        anchors {
            top: parent.top
            left: parent.left
            right: parent.right
            leftMargin: 64
            rightMargin: anchors.leftMargin
        }
        height: 64
        BackButton {
            id: backButton
            anchors {
                left: parent.left
                top: parent.top
                bottom: parent.bottom
                topMargin: 16
                bottomMargin: 16
            }
            onClicked: {
                canGoBack = false
                contentList.currentIndex--
            }
        }
        AdwaitaButton {
            text: "Write to USB disk"
            //color: "#729FCF"
            color: Qt.darker("#729fcf", 1.25)
            textColor: "white"
            width: implicitWidth + 16
            onClicked: dialog.visible = true
            anchors {
                right: parent.right
                top: parent.top
                bottom: parent.bottom
                topMargin: 16
                bottomMargin: 16
            }
        }
    }

    ScrollView {
        anchors {
            fill: parent
            leftMargin: anchors.rightMargin
        }

        contentItem: Item {
            y: 72
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
                        RowLayout {
                            Text {
                                Layout.fillWidth: true
                                anchors.left: parent.left
                                font.pointSize: 11
                                text: "Fedora Workstation 21"
                            }
                            Text {
                                anchors.right: parent.right
                                font.pointSize: 11
                                text: "953MB"
                                color: "gray"
                            }
                        }
                        Text {
                            text: "64bit"
                            color: "gray"
                        }
                        Text {
                            text: "Released on December 21st 2014"
                            font.pointSize: 8
                            color: "gray"
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
                IndicatedImage {
                    Layout.fillWidth: true
                    fillMode: Image.PreserveAspectFit
                    source: "http://fedora.cz/wp-content/uploads/2013/12/fedora-20-gnome-10.png"
                    sourceSize.width: width
                }
            }
        }

        style: ScrollViewStyle {
            incrementControl: Item {}
            decrementControl: Item {}
            corner: Item {
                implicitWidth: 11
                implicitHeight: 11
            }
            scrollBarBackground: Rectangle {
                color: "#dddddd"
                implicitWidth: 11
                implicitHeight: 11
            }
            handle: Rectangle {
                color: "#b3b5b6"
                x: 2
                y: 2
                implicitWidth: 7
                implicitHeight: 7
                radius: 4
            }
            transientScrollBars: true
            handleOverlap: 1
            minimumHandleLength: 10
        }
    }
    DownloadDialog {
        id: dialog
    }
}

