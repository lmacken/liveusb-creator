import QtQuick 2.4
import QtQuick.Controls 1.2
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.1
import QtQuick.Window 2.0

Dialog {
    id: root
    title: "Write " + liveUSBData.currentImage.name + " to USB"

    height: layout.height + 56
    standardButtons: StandardButton.NoButton

    width: 640

    contentItem: Rectangle {
        id: contentWrapper
        anchors.fill: parent
        color: palette.window
        ScrollView {
            anchors.fill: parent
            horizontalScrollBarPolicy: Qt.ScrollBarAlwaysOff
            contentItem: Item {
                width: contentWrapper.width
                height: layout.height + 32
                Column {
                    id: layout
                    spacing: 24
                    clip: true
                    anchors {
                        top: parent.top
                        left: parent.left
                        right: parent.right
                        topMargin: 32
                        leftMargin: 48
                        rightMargin: anchors.leftMargin
                    }
                    Column {
                        id: infoColumn
                        spacing: 4
                        width: parent.width

                        Repeater {
                            model: liveUSBData.currentImage.error
                            RowLayout {
                                width: infoColumn.width
                                spacing: 8
                                Text {
                                    Layout.fillHeight: true
                                    verticalAlignment: Text.AlignVCenter
                                    color: "red"
                                    text: "!!!"
                                    font.pointSize: 14
                                }
                                Text {
                                    Layout.fillHeight: true
                                    Layout.fillWidth: true
                                    verticalAlignment: Text.AlignVCenter
                                    wrapMode: Text.Wrap
                                    text: liveUSBData.currentImage.error[index]
                                }
                            }
                        }


                        Repeater {
                            model: (liveUSBData.currentImage.writer.finished || liveUSBData.currentImage.error.length > 0) ? null : liveUSBData.currentImage.warning
                            RowLayout {
                                width: infoColumn.width
                                spacing: 8
                                Text {
                                    Layout.fillHeight: true
                                    verticalAlignment: Text.AlignVCenter
                                    color: "red"
                                    text: "!"
                                    font.pointSize: 14
                                }
                                Text {
                                    Layout.fillHeight: true
                                    Layout.fillWidth: true
                                    verticalAlignment: Text.AlignVCenter
                                    wrapMode: Text.Wrap
                                    text: liveUSBData.currentImage.warning[index]
                                }
                            }
                        }

                        Repeater {
                            model: liveUSBData.currentImage.error.length > 0 ? null : liveUSBData.currentImage.info
                            RowLayout {
                                width:  infoColumn.width
                                spacing: 8
                                // a rotated exclamation mark instead of an 'i' as for information - that's funny, right... right?!
                                Text {
                                    Layout.fillHeight: true
                                    verticalAlignment: Text.AlignVCenter
                                    color: "blue"
                                    text: "!"
                                    rotation: 180
                                    font.pointSize: 14
                                }
                                Text {
                                    Layout.fillHeight: true
                                    Layout.fillWidth: true
                                    verticalAlignment: Text.AlignVCenter
                                    wrapMode: Text.Wrap
                                    text: liveUSBData.currentImage.info[index]
                                }
                            }
                        }
                    }

                    ColumnLayout {
                        width: parent.width
                        Behavior on y {
                            NumberAnimation {
                                duration: 1000
                            }
                        }

                        Text {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
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
                                progressColor: liveUSBData.currentImage.writer.status == "Checking the source image" ? Qt.lighter("green") : "red"
                            }
                        }
                    }

                    RowLayout {
                        anchors.horizontalCenter: parent.horizontalCenter
                        spacing: 32
                        IndicatedImage {
                            source: liveUSBData.currentImage.logo
                            sourceSize.width: 64
                            sourceSize.height: 64
                            fillMode: Image.PreserveAspectFit
                        }
                        Arrow {
                            id: writeArrow
                            anchors.verticalCenter: parent.verticalCenter
                            height: 14
                            SequentialAnimation {
                                running: liveUSBData.currentImage.writer.running
                                loops: -1
                                onStopped: {
                                    if (liveUSBData.currentImage.writer.finished)
                                        writeArrow.color = "#00dd00"
                                    else
                                        writeArrow.color = "black"
                                }
                                ColorAnimation {
                                    duration: 3500
                                    target: writeArrow
                                    property: "color"
                                    to: "red"
                                }
                                PauseAnimation {
                                    duration: 500
                                }
                                ColorAnimation {
                                    duration: 3500
                                    target: writeArrow
                                    property: "color"
                                    to: "black"
                                }
                                PauseAnimation {
                                    duration: 500
                                }
                            }
                        }
                        AdwaitaComboBox {
                            Layout.preferredWidth: implicitWidth * 2.3
                            model: liveUSBData.usbDriveNames
                            currentIndex: liveUSBData.currentDrive
                            onCurrentIndexChanged: {
                                acceptButton.pressedOnce = false
                                liveUSBData.currentDrive = currentIndex
                            }
                            enabled: !liveUSBData.currentImage.writer.running
                        }
                    }

                    ColumnLayout {
                        width: parent.width
                        spacing: 12
                        RowLayout {
                            height: acceptButton.height
                            width: parent.width
                            AdwaitaButton  {
                                id: optionGroup
                                implicitHeight: parent.height / 8 * 5
                                implicitWidth: parent.height / 8 * 5
                                Layout.alignment: Qt.AlignVCenter
                                checkable: true
                                checked: false
                                enabled: liveUSBData.optionNames && liveUSBData.optionNames[0] && !liveUSBData.currentImage.writer.running
                                onEnabledChanged: {
                                    if (!liveUSBData.currentImage.writer.running)
                                        checked = false
                                }
                                Text {
                                    anchors.fill: parent
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                    text: "+"
                                    font.bold: true
                                    font.pointSize: 12
                                }
                            }

                            Text {
                                Layout.fillHeight: true
                                verticalAlignment: Text.AlignVCenter
                                text: "Advanced options"
                                enabled: optionGroup.enabled
                                MouseArea {
                                    anchors.fill: parent
                                    onClicked: optionGroup.checked = !optionGroup.checked
                                }
                            }

                            Item {
                                Layout.fillWidth: true
                                height: 1
                            }

                            AdwaitaButton {
                                id: cancelButton
                                anchors {
                                    right: acceptButton.left
                                    top: parent.top
                                    bottom: parent.bottom
                                    rightMargin: 6
                                }
                                text: "Cancel"
                                enabled: !liveUSBData.currentImage.writer.running
                                onClicked: {
                                    liveUSBData.currentImage.download.cancel()
                                    liveUSBData.currentImage.writer.cancel()
                                    acceptButton.pressedOnce = false
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
                                property bool pressedOnce: false
                                color: "red"
                                textColor: enabled ? "white" : palette.text
                                enabled: liveUSBData.currentImage.readyToWrite && !liveUSBData.currentImage.writer.running
                                text: pressedOnce ? "Are you sure?" : "Write to disk"
                                onClicked: {
                                    if(pressedOnce || !liveUSBData.currentImage.warning || liveUSBData.currentImage.warning.length == 0) {
                                        liveUSBData.currentImage.write()
                                        pressedOnce = false
                                        optionGroup.checked = false
                                    }
                                    else {
                                        pressedOnce = true
                                    }
                                }
                            }
                        }
                        Column {
                            id: advancedOptions
                            Repeater {
                                id: groupLayoutRepeater
                                model: optionGroup.checked ? liveUSBData.optionValues : null
                                CheckBox {
                                    checked: liveUSBData.optionValues[index]
                                    enabled: !liveUSBData.currentImage.writer.running
                                    height: 20
                                    width: implicitWidth
                                    text: liveUSBData.optionNames[index]
                                    onClicked: {
                                        acceptButton.pressedOnce = false
                                        liveUSBData.setOption(index, checked)
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
