import QtQuick 2.0

Item {
    width: parent.width
    height: $(84)
    Rectangle {
        width: parent.width - $(2)
        height: index == 0 ? parent.height - $(1) : parent.height
        x: $(1)
        y: index == 0 ? $(1) : 0
        radius: $(4)
        color: "transparent"
        Item {
            id: iconRect
            anchors {
                top: parent.top
                left: parent.left
                bottom: parent.bottom
                leftMargin: $(32)
                topMargin: $(16)
                bottomMargin: anchors.topMargin
            }
            width: height
            IndicatedImage {
                fillMode: Image.PreserveAspectFit
                source: release.logo
                sourceSize.height: parent.height
                sourceSize.width: parent.width
            }
        }
        Item {
            id: textRect
            anchors {
                verticalCenter: parent.verticalCenter
                left: iconRect.right
                right: arrow.left
                bottom: parent.bottom
                leftMargin: $(28)
                rightMargin: $(14)
            }
            Text {
                font.pixelSize: $(12)
                text: release.name
                anchors {
                    bottom: parent.verticalCenter
                    left: parent.left
                    bottomMargin: $(2)
                }
                // font.weight: Font.Bold
            }
            Text {
                font.pixelSize: $(12)
                text: release.summary
                anchors {
                    top: parent.verticalCenter
                    left: parent.left
                    right: parent.right
                    topMargin: $(2)
                }
                wrapMode: Text.Wrap
                color: "#a1a1a1"
                // font.weight: Font.Bold
            }
        }
        Arrow {
            id: arrow
            visible: !release.isLocal
            anchors {
                verticalCenter: parent.verticalCenter
                right: parent.right
                rightMargin: $(20)
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
                root.stepForward(release.index)
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
