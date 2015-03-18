import QtQuick 2.4
import QtQuick.Controls 1.3
import QtQuick.Controls.Styles 1.3
import QtQuick.Layouts 1.1

Item {
    id: root

    property alias currentIndex: osListView.currentIndex
    property bool viewFullList: false
    property real fadeDuration: 200

    signal stepForward(int index)

    anchors.fill: parent
    clip: true

    Rectangle {
        enabled: root.viewFullList
        opacity: root.viewFullList ? 1.0 : 0.0
        id: searchBox
        border {
            color: searchInput.activeFocus ? "#4a90d9" : "#c3c3c3"
            width: 1
        }
        radius: 6
        color: "white"
        anchors {
            top: parent.top
            left: parent.left
            right: archSelect.left
            topMargin: 12
            leftMargin: 64
            rightMargin: 4
        }
        height: 36

        Item {
            id: magnifyingGlass
            anchors {
                left: parent.left
                leftMargin: (parent.height - height) / 2
                verticalCenter: parent.verticalCenter
            }
            height: childrenRect.height + 3
            width: childrenRect.width + 2

            Rectangle {
                height: 11
                antialiasing: true
                width: height
                radius: height / 2
                color: "black"
                Rectangle {
                    height: 7
                    antialiasing: true
                    width: height
                    radius: height / 2
                    color: "white"
                    anchors.centerIn: parent
                }
                Rectangle {
                    height: 2
                    width: 6
                    radius: 2
                    x: 8
                    y: 11
                    rotation: 45
                    color: "black"
                }
            }
        }
        TextInput {
            id: searchInput
            anchors {
                left: magnifyingGlass.right
                top: parent.top
                bottom: parent.bottom
                right: parent.right
                margins: 8
            }
            Text {
                anchors.fill: parent
                color: "light gray"
                text: "find an operating system image"
                visible: !parent.activeFocus && parent.text.length == 0
                verticalAlignment: Text.AlignVCenter
            }
            verticalAlignment: TextInput.AlignVCenter

            clip: true
        }
    }

    AdwaitaComboBox {
        enabled: root.viewFullList
        opacity: root.viewFullList ? 1.0 : 0.0
        Behavior on opacity {
            NumberAnimation {
                duration: root.fadeDuration
            }
        }

        id: archSelect
        anchors {
            right: parent.right
            top: parent.top
            rightMargin: 64
            topMargin: 12
        }
        height: 36
        width: 148
        model: liveUSBData.releaseProxyModel.possibleArchs
    }

    Rectangle {
        clip: true
        z: -1
        anchors {
            top: parent.top
            left: parent.left
            right: parent.right
            topMargin: 54
            rightMargin: 64
            leftMargin: anchors.rightMargin
        }
        border {
            color: "#c3c3c3"
            width: 1
        }
        height: root.viewFullList ? parent.height - 54 + 4 : parent.height - 108
        Behavior on height {
            NumberAnimation {
                duration: root.fadeDuration
            }
        }

        Item {
            anchors.fill: parent
            enabled: !root.viewFullList
            opacity: root.viewFullList ? 0.0 : 1.0
            Behavior on opacity {
                NumberAnimation {
                    duration: root.fadeDuration
                }
            }
            Column {
                id: selectedOsColumn
                anchors {
                    top: parent.top
                    left: parent.left
                    right: parent.right
                }
                Repeater {
                    model: liveUSBData.titleReleaseModel
                    delegate: imageDelegate
                }
            }
            Rectangle {
                anchors {
                    top: selectedOsColumn.bottom
                    bottom: parent.bottom
                    left: parent.left
                    right: parent.right
                    margins: 1
                }
                radius: 3
                Column {
                    anchors.centerIn: parent
                    spacing: 2
                    Repeater {
                        model: 3
                        Rectangle {
                            height: 4
                            width: 4
                            color: "#bebebe"
                        }
                    }
                }
                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        root.viewFullList = true
                    }
                    onPressed: {
                        parent.color = "#ededed"
                    }
                    onReleased: {
                        parent.color = "transparent"
                    }
                    onCanceled: {
                        parent.color = "transparent"
                    }
                }
            }
        }

        radius: 6
        color: "white"
    }

    ScrollView {
        id: fullList
        enabled: root.viewFullList
        opacity: root.viewFullList ? 1.0 : 0.0
        Behavior on opacity {
            NumberAnimation {
                duration: root.fadeDuration
            }
        }
        anchors.fill: parent
        ListView {
            id: osListView
            clip: true
            anchors {
                fill: parent
                leftMargin: 64
                rightMargin: anchors.leftMargin
                topMargin: 54
                bottomMargin: -anchors.topMargin
            }
            footer: Item {
                height: 54
            }

            model: liveUSBData.releaseProxyModel
            delegate: imageDelegate
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

    Component {
        id: imageDelegate
        Item {
            width: parent.width
            height: 84
            Rectangle {
                width: parent.width - 2
                height: index == 0 ? parent.height - 1 : parent.height
                x: 1
                y: index == 0 ? 1 : 0
                radius: 4
                color: "transparent"
                IndicatedImage {
                    id: iconRect
                    anchors {
                        top: parent.top
                        left: parent.left
                        bottom: parent.bottom
                        leftMargin: 32
                        topMargin: 16
                        bottomMargin: anchors.topMargin
                    }
                    width: height
                    smooth: true
                    fillMode: Image.PreserveAspectFit

                    source: release.logo
                }
                Item {
                    id: textRect
                    anchors {
                        verticalCenter: parent.verticalCenter
                        left: iconRect.right
                        leftMargin: 28
                    }
                    Text {
                        text: release.name
                        anchors {
                            bottom: parent.verticalCenter
                            left: parent.left
                            bottomMargin: 2
                        }
                        // font.weight: Font.Bold
                    }
                    Text {
                        text: release.shortDescription
                        anchors {
                            top: parent.verticalCenter
                            left: parent.right
                            topMargin: 2
                        }
                        color: "#a1a1a1"
                        // font.weight: Font.Bold
                    }
                }
                Arrow {
                    visible: !release.isLocal
                    anchors {
                        verticalCenter: parent.verticalCenter
                        right: parent.right
                        rightMargin: 20
                    }
                }
                Rectangle {
                    height: 1
                    color: "#c3c3c3"
                    width: parent.width
                    anchors.bottom: parent.bottom
                }
                MouseArea {
                    anchors.fill: parent
                    hoverEnabled: true
                    onHoveredChanged: {
                        if (containsMouse && !pressed)
                            parent.color = "#f8f8f8"
                        if (!containsMouse)
                            parent.color = "transparent"
                    }
                    onClicked: {
                        root.currentIndex = index
                        root.stepForward(index)
                    }
                    onPressed: {
                        parent.color = "#ededed"
                    }
                    onReleased: {
                        parent.color = "transparent"
                    }
                    onCanceled: {
                        parent.color = "transparent"
                    }
                }
            }
        }
    }
}
