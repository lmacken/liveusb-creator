import QtQuick 2.0
import QtQuick.Controls 1.2
import QtQuick.Controls.Styles 1.2
import QtQuick.Layouts 1.1
import QtQuick.Dialogs 1.2

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
            color: "#729fcf"
            textColor: "white"
            width: implicitWidth + 16
            onClicked: {
                dlDialog.visible = true
                liveUSBData.currentImage.get()
            }
            enabled: !liveUSBData.currentImage.isLocal || liveUSBData.currentImage.readyToWrite
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
                    Item {
                        width: 64
                        height: 64
                        IndicatedImage {
                            id: iconRect
                            anchors.centerIn: parent
                            source: liveUSBData.currentImage.logo
                            sourceSize.width: parent.width
                            sourceSize.height: parent.height
                            fillMode: Image.PreserveAspectFit
                        }
                    }

                    ColumnLayout {
                        Layout.alignment: Qt.AlignLeft
                        spacing: 8
                        RowLayout {
                            Text {
                                Layout.fillWidth: true
                                anchors.left: parent.left
                                font.pointSize: 11
                                text: liveUSBData.currentImage.name
                            }
                            Text {
                                anchors.right: parent.right
                                font.pointSize: 11
                                property double size: liveUSBData.currentImage.size
                                text: size <= 0 ? "" :
                                      (size < 1024) ? (size + " B") :
                                      (size < (1024 * 1024)) ? ((size / 1024).toFixed(1) + " KB") :
                                      (size < (1024 * 1024 * 1024)) ? ((size / 1024 / 1024).toFixed(1) + " MB") :
                                      ((size / 1024 / 1024 / 1024).toFixed(1) + " GB")

                                color: "gray"
                            }
                        }
                        Text {
                            text: liveUSBData.currentImage.arch
                            color: "gray"

                            AdwaitaButton {
                                text: "Select the file"
                                Layout.alignment: Qt.AlignHCenter
                                visible: liveUSBData.currentImage.isLocal
                                onClicked: {
                                    fileDialog.visible = false // for some reason it got stuck in the closed state once in a while, so ensure it's actually closed
                                    fileDialog.visible = true
                                }
                                width: implicitWidth + 16
                            }
                        }
                        Text {
                            // I'm sorry, everyone, I can't find a better way to determine if the date is valid
                            text: liveUSBData.currentImage.releaseDate.toLocaleDateString().length > 0 ? ("Released on " + liveUSBData.currentImage.releaseDate.toLocaleDateString()) : ""
                            font.pointSize: 8
                            color: "gray"
                        }
                    }
                }
                Text {
                    Layout.fillWidth: true
                    width: Layout.width
                    wrapMode: Text.WordWrap
                    text: liveUSBData.currentImage.isLocal ?
                              ("Selected image: " + (liveUSBData.currentImage.path ? (((String)(liveUSBData.currentImage.path)).split("/").slice(-1)[0]) : "None"))
                              : liveUSBData.currentImage.fullDescription
                    font.pointSize: 9
                }
                Repeater {
                    id: screenshotRepeater
                    model: liveUSBData.currentImage.screenshots
                    IndicatedImage {
                        Layout.fillWidth: true
                        fillMode: Image.PreserveAspectFit
                        source: screenshotRepeater.model[index]
                        sourceSize.width: width
                    }
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
        id: dlDialog
    }
    FileDialog {
        id: fileDialog
        nameFilters: [ "Image files (*.iso)", "All files (*)"]
        onAccepted: {
            liveUSBData.currentImage.path = fileUrl
        }
    }
}

