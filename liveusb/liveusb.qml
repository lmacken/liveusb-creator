import QtQuick 2.4
import QtQuick.Controls 1.3
import QtQuick.Window 2.2
import QtQuick.Dialogs 1.2

import "components"

ApplicationWindow {
    id: mainWindow
    width: 800
    height: 480
    title: "OS Boot imager"

    SystemPalette {
        id: palette
    }

    flags: Qt.TransparentMode
    color: "transparent"


    property int currentImageIndex: 1
    property bool canGoBack: false

    Behavior on x {
        NumberAnimation {
            duration: 80
        }
    }
    Behavior on y {
        NumberAnimation {
            duration: 80
        }
    }

    ListModel {
        id: selectedOsList
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
    }

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

    Rectangle {
        anchors.fill: parent
        color: palette.window
        //radius: 8
        clip: true
/*
        Rectangle {
            id: toolBar
            height: 48
            z: 2
            clip: true

            color: "transparent"

            Rectangle {
                width: parent.width
                anchors.bottom: parent.bottom
                height: 1
                color: "#a1a1a1"
            }

            anchors {
                top: parent.top
                right: parent.right
                left: parent.left
            }

            MouseArea {
                id: titleMouse
                anchors.fill: parent
                property real startX: 0
                property real startY: 0
                onPressed: {
                    startX = mouse.x
                    startY = mouse.y
                }
                onPositionChanged: {
                    mainWindow.x -= startX - mouseX
                    mainWindow.y -= startY - mouseY
                }
            }

            BackButton {
                id: backButton
                visible: canGoBack
                width: height
                anchors {
                    left: parent.left
                    top: parent.top
                    bottom: parent.bottom
                    margins: 6
                }
                onClicked: {
                    canGoBack = false
                    contentList.currentIndex--
                }
            }

            Text {
                text: "OS Boot Imager"
                anchors.centerIn: parent
            }


            MenuButton {
                id: menuButton
                width: height
                anchors {
                    right: parent.right
                    // right: spacer.left
                    top: parent.top
                    bottom: parent.bottom
                    margins: 6
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

            QuitButton {
                id: quitButton
                //flat: true
                anchors {
                    right: parent.right
                    top: parent.top
                    bottom: parent.bottom
                    margins: 6
                }
                width: height
                onClicked: mainWindow.close()
            }

        }*/

        ListView {
            id: contentList
            anchors{
                top: parent.top
                bottom: parent.bottom
                left: parent.left
                right: parent.right
            }
            model: ["components/ImageList.qml", "components/ImageDetails.qml"]
            orientation: ListView.Horizontal
            snapMode: ListView.SnapOneItem
            interactive: false
            highlightMoveVelocity: 3 * contentList.width
            cacheBuffer: 2*width
            delegate: Item {
                id: contentComponent
                width: contentList.width
                height: contentList.height
                Loader {
                    id: contentLoader
                    source: contentList.model[index]
                    anchors.fill: parent
                }
                Connections {
                    target: contentLoader.item
                    onStepForward: {
                        contentList.currentIndex = 1
                        canGoBack = true
                    }
                }
            }
        }
    }
}

