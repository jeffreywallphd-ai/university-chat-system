import SwiftUI

struct MapView: View {
    var body: some View {
        VStack(spacing: 20) {
            Text("Campus Wayfinding")
                .font(.largeTitle)
                .foregroundColor(.blue)

            Image(systemName: "map")
                .resizable()
                .frame(width: 200, height: 200)
                .foregroundColor(.secondary)
        }
    }
}
