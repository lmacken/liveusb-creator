import QtQuick 2.4
import QtQuick.Controls 1.3
import QtQuick.Window 2.2
import QtQuick.Dialogs 1.2

import "components"

ApplicationWindow {
    width: 800
    height: 480

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
            icon: ""
            hasDetails: true
        }
        ListElement {
            name: "Fedora Workstation"
            description: "Fedora Workstation 20 64bit"
            icon: ""
            hasDetails: true
        }
        ListElement {
            name: "Ubuntu Desktop"
            description: "Ubuntu 14.04.1 LTS 64bit"
            icon: ""
            hasDetails: true
        }
        ListElement {
            name: "Ubuntu Desktop"
            description: "Ubuntu 14.10 64bit"
            icon: ""
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
        }

    }

    ImageList {
        anchors {
            top: parent.top
            bottom: parent.bottom
            left: parent.left
            right: parent.right
            topMargin: 48
            bottomMargin: anchors.topMargin
            leftMargin: 64
            rightMargin: anchors.leftMargin
        }
    }
}

