import QtQuick 2.4
import QtQuick.Controls 1.3
import QtQuick.Window 2.2
import QtQuick.Dialogs 1.2

import "components"

ApplicationWindow {
    id: mainWindow
    width: 800
    height: 480

    SystemPalette {
        id: palette
    }

    property int currentImageIndex: 1
    property bool canGoBack: false

    ListModel {
        id: osList
        ListElement {
            name: "Custom OS..."
            description: "<pick from file chooser>"
            icon: ""
            hasDetails: false
        }
        ListElement {
            name: "Fedora Workstation"
            description: "Fedora Workstation 21 64bit"
            icon: "http://upload.wikimedia.org/wikipedia/commons/3/3f/Fedora_logo.svg"
            hasDetails: true
        }
        ListElement {
            name: "Fedora Workstation"
            description: "Fedora Workstation 20 64bit"
            icon: "http://upload.wikimedia.org/wikipedia/commons/3/3f/Fedora_logo.svg"
            hasDetails: true
        }
        ListElement {
            name: "Ubuntu Desktop"
            description: "Ubuntu 14.04.1 LTS 64bit"
            icon: "http://logonoid.com/images/ubuntu-logo.png"
            hasDetails: true
        }
        ListElement {
            name: "Ubuntu Desktop"
            description: "Ubuntu 14.10 64bit"
            icon: "http://logonoid.com/images/ubuntu-logo.png"
            hasDetails: true
        }
    }

    toolBar: ToolBar {
        id: toolBar
        height: 48
        z: 2

        anchors {
            top: parent.top
            right: parent.right
            left: parent.left
        }

        Button {
            id: backButton
            visible: canGoBack
            width: height
            anchors {
                left: parent.left
                top: parent.top
                bottom: parent.bottom
                margins: 6
            }
            Item {
                anchors.centerIn: parent
                rotation: -45
                transformOrigin: Item.Center
                width: 10
                height: 10
                Rectangle {
                    x: 1.5
                    y: 1.5
                    width: 2
                    height: 9
                    radius: 2
                    color: "#444444"
                }
                Rectangle {
                    y: 1.5
                    x: 1.5
                    width: 9
                    height: 2
                    radius: 2
                    color: "#444444"
                }
            }
            onClicked: {
                canGoBack = false
                contentLoader.source = "components/ImageList.qml"
            }
        }

        Text {
            text: "OS Boot Imager"
            anchors.centerIn: parent
        }

        ComboBox {
            anchors {
                right: searchButton.left
                top: parent.top
                bottom: parent.bottom
                margins: 6
            }
            width: 148
            model: ["64bit (detected)", "32bit"]
        }

        Button {
            id: searchButton
            width: height
            anchors {
                right: spacer.left
                top: parent.top
                bottom: parent.bottom
                margins: 6
            }
            Item {
                anchors.centerIn: parent
                width: 10
                height: 10
                Column {
                    spacing: 2
                    Repeater {
                        model: 3
                        delegate: Rectangle {
                            height: 2
                            width: 10
                            radius: 2
                            color: "#444444"
                        }
                    }
                }
            }
        }

        Rectangle {
            id: spacer
            width: 1
            color: "#c3c3c3"
            anchors {
                right: quitButton.left
                top: parent.top
                bottom: parent.bottom
                margins: 6
            }
        }

        Button {
            id: quitButton
            //flat: true
            anchors {
                right: parent.right
                top: parent.top
                bottom: parent.bottom
                margins: 6
            }
            width: height
            Item {
                anchors.fill: parent
                rotation: 45
                transformOrigin: Item.Center
                Rectangle {
                    width: 2
                    height: 12
                    radius: 1
                    anchors.centerIn: parent
                    color: "#a1a1a1"
                }
                Rectangle {
                    width: 12
                    height: 2
                    radius: 1
                    anchors.centerIn: parent
                    color: "#a1a1a1"
                }
            }
            onClicked: mainWindow.close()
        }

    }

    Loader {
        id: contentLoader
        anchors {
            fill: parent
        }

        source: "components/ImageList.qml"
    }
    Connections {
        target: contentLoader.item
        onStepForward: {
            currentImageIndex = index
            canGoBack = true
            contentLoader.source = "components/ImageDetails.qml"
        }
    }
}

