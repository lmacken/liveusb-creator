import QtQuick 2.4
import QtQuick.Controls 1.3
import QtQuick.Controls.Styles 1.3

Item {
    id: root

    property alias currentIndex: osListView.currentIndex
    signal stepForward(int index)

    anchors.fill: parent
    clip: true

    Rectangle {
        id: searchBox
        border {
            color: "#c3c3c3"
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
                visible: !parent.focus
                verticalAlignment: Text.AlignVCenter
            }
            verticalAlignment: TextInput.AlignVCenter

            clip: true
        }
    }

    AdwaitaComboBox {
        id: archSelect
        anchors {
            right: parent.right
            top: parent.top
            rightMargin: 64
            topMargin: 12
        }
        height: 36
        width: 148
        model: ["64bit (detected)", "32bit"]
    }

    Rectangle {
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
        height: parent.height - 54 + 4

        radius: 6
        color: "white"
    }

    ScrollView {
        anchors.fill: parent
        ListView {
            id: osListView
            clip: true
            anchors {
                fill: parent
                topMargin: 54
                bottomMargin: -54
            }
            footer: Item {
                height: 54
            }

            model: osList
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
                width: parent.width - 2 - 128
                height: parent.height
                x: 64 + 1
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

                    source: icon
                }
                Item {
                    id: textRect
                    anchors {
                        verticalCenter: parent.verticalCenter
                        left: iconRect.right
                        leftMargin: 28
                    }
                    Text {
                        text: name
                        anchors {
                            bottom: parent.verticalCenter
                            left: parent.left
                            bottomMargin: 2
                        }
                        // font.weight: Font.Bold
                    }
                    Text {
                        text: description
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
                    visible: hasDetails
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
